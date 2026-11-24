"""
Unit tests for the Respiratory Acoustic Preprocessing and Inference Module.
Tests pure-NumPy log-mel spectrogram extraction, CRNN architecture shapes,
and acoustic class inference (normal, crackle, wheeze, both).
"""
import sys
import os
import unittest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.respiratory.preprocessing.audio import compute_log_mel_spectrogram, pad_or_truncate
from ml.respiratory.models.crnn import CompactRespiratoryCRNN
from ml.respiratory.inference.predict import respiratory_inference_service


class TestRespiratoryModule(unittest.TestCase):
    def test_spectrogram_dimensions(self):
        # 5 seconds of synthetic audio at 16 kHz
        sr = 16000
        synthetic_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 5, 5 * sr)).astype(np.float32)
        mel_spec = compute_log_mel_spectrogram(synthetic_audio, sr=sr, n_mels=64)
        
        # Check Mel bins
        self.assertEqual(mel_spec.shape[0], 64)
        self.assertGreater(mel_spec.shape[1], 100)

    def test_crnn_forward_pass(self):
        model = CompactRespiratoryCRNN(n_mels=64, n_classes=4)
        dummy_spec = np.random.randn(64, 156).astype(np.float32)
        probs, emb = model.forward(dummy_spec)
        
        self.assertEqual(probs.shape, (4,))
        self.assertEqual(emb.shape, (768,))
        self.assertAlmostEqual(float(np.sum(probs)), 1.0, places=4)

    def test_audio_cropping(self):
        long_audio = np.ones(100000, dtype=np.float32)
        cropped = pad_or_truncate(long_audio, target_length=80000)
        self.assertEqual(len(cropped), 80000)


if __name__ == "__main__":
    unittest.main()
