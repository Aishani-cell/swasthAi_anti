"""
Respiratory Audio Signal Preprocessing & Log-Mel Spectrogram Generation
Pure-Python & NumPy implementation supporting standard ICBHI 2017 audio protocols:
- 16 kHz sample rate
- 64 Mel filterbank bins
- 5.0-second standardization window
- Amplitude peak normalization
- Energy-based signal-to-noise quality check
"""
import wave
import struct
import math
import numpy as np
from typing import Tuple, Optional, Dict, Any

def read_wav_file(file_path: str) -> Tuple[np.ndarray, int]:
    """
    Reads a standard WAV file using Python's built-in wave module.
    Returns: (mono_float_samples, sample_rate)
    """
    with wave.open(file_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    # Decode bytes to numpy array according to sample width
    if sampwidth == 2:  # 16-bit PCM
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 1:  # 8-bit PCM
        samples = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sampwidth == 4:  # 32-bit PCM
        samples = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    # Convert to mono by averaging channels if stereo
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    return samples, framerate

def resample_signal(samples: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """Simple linear interpolation resampler to target sample rate."""
    if orig_sr == target_sr or len(samples) == 0:
        return samples
    duration = len(samples) / float(orig_sr)
    target_len = int(round(duration * target_sr))
    orig_indices = np.linspace(0, len(samples) - 1, target_len)
    return np.interp(orig_indices, np.arange(len(samples)), samples).astype(np.float32)

def pad_or_truncate(samples: np.ndarray, target_length: int) -> np.ndarray:
    """Standardizes signal length to target_length."""
    if len(samples) > target_length:
        return samples[:target_length]
    elif len(samples) < target_length:
        return np.pad(samples, (0, target_length - len(samples)), mode='constant')
    return samples

def hz_to_mel(hz: float) -> float:
    return 2595.0 * math.log10(1.0 + hz / 700.0)

def mel_to_hz(mel: float) -> float:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

def create_mel_filterbank(n_mels: int = 64, n_fft: int = 512, sr: int = 16000) -> np.ndarray:
    """Constructs triangular Mel filterbank matrix of shape [n_mels, n_fft // 2 + 1]."""
    f_min = 50.0
    f_max = float(sr // 2)
    mel_min = hz_to_mel(f_min)
    mel_max = hz_to_mel(f_max)
    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = np.array([mel_to_hz(m) for m in mel_points])
    bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)

    n_bins = n_fft // 2 + 1
    fbank = np.zeros((n_mels, n_bins), dtype=np.float32)

    for i in range(1, n_mels + 1):
        left = bin_points[i - 1]
        center = bin_points[i]
        right = bin_points[i + 1]

        if center > left:
            fbank[i - 1, left:center] = (np.arange(left, center) - left) / float(center - left)
        if right > center:
            fbank[i - 1, center:right] = (right - np.arange(center, right)) / float(right - center)

    return fbank

def compute_log_mel_spectrogram(
    samples: np.ndarray,
    sr: int = 16000,
    n_mels: int = 64,
    n_fft: int = 512,
    hop_length: int = 256
) -> np.ndarray:
    """
    Computes Log-Mel Spectrogram matrix of shape [n_mels, time_steps].
    """
    # STFT with Hanning window
    window = np.hanning(n_fft)
    num_frames = max(1, (len(samples) - n_fft) // hop_length + 1)
    
    spec = np.zeros((n_fft // 2 + 1, num_frames), dtype=np.float32)
    for t in range(num_frames):
        start = t * hop_length
        chunk = samples[start:start + n_fft]
        if len(chunk) < n_fft:
            chunk = np.pad(chunk, (0, n_fft - len(chunk)))
        fft_res = np.fft.rfft(chunk * window)
        spec[:, t] = np.abs(fft_res) ** 2.0  # Power spectrum

    # Apply Mel filterbank
    fbank = create_mel_filterbank(n_mels=n_mels, n_fft=n_fft, sr=sr)
    mel_spec = np.dot(fbank, spec)

    # Logarithmic compression with floor
    log_mel = np.log10(np.maximum(mel_spec, 1e-6))
    
    # Per-spectrogram mean-variance normalization
    mean = np.mean(log_mel)
    std = np.std(log_mel) + 1e-6
    return ((log_mel - mean) / std).astype(np.float32)

def fit_mel_frames(log_mel: np.ndarray, n_frames: int = 128) -> np.ndarray:
    """Crop or zero-pad a log-mel matrix to [n_mels, n_frames]."""
    n_mels, steps = log_mel.shape
    if steps == n_frames:
        return log_mel
    if steps > n_frames:
        start = (steps - n_frames) // 2
        return log_mel[:, start:start + n_frames]
    return np.pad(log_mel, ((0, 0), (0, n_frames - steps)), mode="constant").astype(np.float32)


def slice_audio(samples: np.ndarray, sr: int, start_sec: float, end_sec: float) -> np.ndarray:
    start = max(0, int(start_sec * sr))
    end = min(len(samples), int(end_sec * sr))
    if end <= start:
        return np.zeros(1, dtype=np.float32)
    return samples[start:end].astype(np.float32)


def cycle_to_log_mel(
    samples: np.ndarray,
    sr: int,
    start_sec: float,
    end_sec: float,
    target_sr: int = 16000,
    n_mels: int = 64,
    n_frames: int = 128,
) -> np.ndarray:
    clip = slice_audio(samples, sr, start_sec, end_sec)
    clip = resample_signal(clip, sr, target_sr)
    clip = pad_or_truncate(clip, target_sr)  # 1 second minimum context, then mel frames are standardized
    peak = float(np.max(np.abs(clip))) if len(clip) else 0.0
    if peak > 0:
        clip = clip / peak
    log_mel = compute_log_mel_spectrogram(clip, sr=target_sr, n_mels=n_mels)
    return fit_mel_frames(log_mel, n_frames=n_frames)


def sliding_windows(duration_sec: float, window_sec: float = 5.0, hop_sec: float = 2.5) -> list:
    if duration_sec <= window_sec:
        return [(0.0, duration_sec)]
    windows = []
    start = 0.0
    while start + 0.5 < duration_sec:
        end = min(duration_sec, start + window_sec)
        windows.append((start, end))
        if end >= duration_sec:
            break
        start += hop_sec
    return windows


def preprocess_respiratory_audio(
    file_path: str,
    target_sr: int = 16000,
    segment_duration: float = 5.0,
    n_mels: int = 64
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Full preprocessing pipeline from audio file to standardized Log-Mel tensor.
    Returns: (log_mel_matrix, quality_metrics)
    """
    samples, sr = read_wav_file(file_path)
    samples = resample_signal(samples, sr, target_sr)
    target_samples = int(target_sr * segment_duration)
    
    # Check signal energy
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) > 0 else 0.0
    quality = "VALID"
    if rms < 0.001:
        quality = "LOW_AMPLITUDE_WARNING"

    samples = pad_or_truncate(samples, target_samples)
    
    # Peak normalization
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = samples / max_val

    log_mel = compute_log_mel_spectrogram(samples, sr=target_sr, n_mels=n_mels)
    
    meta = {
        "sample_rate": target_sr,
        "duration_seconds": round(len(samples) / float(target_sr), 2),
        "rms_energy": round(rms, 5),
        "quality_status": quality,
        "spectrogram_shape": list(log_mel.shape)
    }
    
    return log_mel, meta
