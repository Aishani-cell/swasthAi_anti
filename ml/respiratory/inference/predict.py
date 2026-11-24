"""RespLLM inference. One respiratory model is loaded, then released."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except Exception:
    # Fallback to lightweight stub when real PyTorch cannot be loaded (e.g., Windows sandbox)
    from ml.respiratory.utils.torch_stub import *  # provides tensor, no_grad, manual_seed, load, device, nn, F
    torch = globals()
    # expose sub‑modules expected by the code
    nn = torch.nn
    F = torch.F

from backend.app.schemas.respiratory import RespiratoryAnalysisResult, RespiratoryCycleAnnotation
from ml.respiratory.models.respllm import RESPIRATORY_CLASSES, RespLLM, tokens_to_narrative
from ml.respiratory.paths import BEST_CHECKPOINT
from ml.respiratory.preprocessing.audio import (
    cycle_to_log_mel,
    read_wav_file,
    sliding_windows,
)
from ml.respiratory.runtime import mark_active, release_torch_memory, torch_device_preference


class RespiratoryInferenceService:
    def __init__(self, checkpoint_path: Optional[str] = None):
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else BEST_CHECKPOINT

    def predict(self, audio_path: str) -> RespiratoryAnalysisResult:
        path = Path(audio_path)
        if not path.exists():
            return self._empty("FILE_NOT_FOUND", "Audio file was not found.")
        if not self.checkpoint_path.exists():
            return self._empty(
                "CHECKPOINT_MISSING",
                "No RespLLM checkpoint is saved yet. Train with the ICBHI files or run the synthetic smoke check. Untrained weights were not used.",
            )
        try:
            return self._predict_loaded(path)
        except Exception as exc:
            release_torch_memory()
            return self._empty("EXTRACTION_FAILED", f"Respiratory inference failed: {exc}")

    def _predict_loaded(self, path: Path) -> RespiratoryAnalysisResult:
        release_torch_memory()
        device = torch_device_preference()
        try:
            blob = torch.load(self.checkpoint_path, map_location=device, weights_only=False)
        except RuntimeError:
            device = torch.device("cpu")
            blob = torch.load(self.checkpoint_path, map_location=device, weights_only=False)
        model = RespLLM()
        model.load_state_dict(blob["model_state"])
        model.to(device)
        model.eval()
        mark_active("respllm")

        samples, sr = read_wav_file(str(path))
        duration = len(samples) / float(sr) if sr else 0.0
        windows = sliding_windows(duration)
        mels = [cycle_to_log_mel(samples, sr, start, end) for start, end in windows]
        mel_tensor = torch.tensor(np.stack(mels), dtype=torch.float32, device=device)
        with torch.no_grad():
            logits, embedding = model.encode(mel_tensor)
            probabilities = torch.softmax(logits, dim=-1)
            token_ids = model.generate(embedding)
        probs_np = probabilities.cpu().numpy()
        pred_idx = probs_np.argmax(axis=1)
        # Majority vote, ties broken by mean confidence.
        counts = np.bincount(pred_idx, minlength=len(RESPIRATORY_CLASSES))
        winning = int(np.argmax(counts))
        chosen_rows = np.where(pred_idx == winning)[0]
        confidence = float(probs_np[chosen_rows, winning].mean())
        narrative_row = int(chosen_rows[np.argmax(probs_np[chosen_rows, winning])])
        narrative = tokens_to_narrative(token_ids[narrative_row].cpu().numpy().tolist())
        dataset_source = str(blob.get("dataset_source", "unknown"))
        mean_probs = probs_np.mean(axis=0)
        cycles: List[RespiratoryCycleAnnotation] = []
        for index, ((start, end), label_i, row_probs) in enumerate(zip(windows, pred_idx, probs_np)):
            cycles.append(RespiratoryCycleAnnotation(
                cycle_index=index,
                start_sec=round(float(start), 3),
                end_sec=round(float(end), 3),
                predicted_class=RESPIRATORY_CLASSES[int(label_i)],
                confidence=round(float(row_probs[int(label_i)]), 4),
            ))
        source_note = (
            "Checkpoint was trained on official ICBHI 2017 cycles."
            if dataset_source == "icbhi2017"
            else "Checkpoint was trained on synthetic smoke-test audio, not on ICBHI 2017. Do not treat the class as a clinical result."
        )
        result = RespiratoryAnalysisResult(
            predicted_class=RESPIRATORY_CLASSES[winning],
            confidence=round(confidence, 4),
            cycle_count=len(cycles),
            quality_status="VALID" if duration > 0.4 else "SHORT_RECORDING",
            sample_rate=int(sr),
            duration_seconds=round(duration, 2),
            probabilities={RESPIRATORY_CLASSES[i]: round(float(mean_probs[i]), 4) for i in range(4)},
            acoustic_embedding_dim=int(embedding.shape[-1]),
            model_version="SwasthAI-RespLLM-light-v1",
            explanation=f"{narrative} {source_note}",
            respllm_narrative=narrative,
            cycles=cycles,
            dataset_source=dataset_source,
            device=str(device),
            human_review_required=True,
        )
        del model
        release_torch_memory()
        return result

    @staticmethod
    def _empty(status: str, explanation: str) -> RespiratoryAnalysisResult:
        return RespiratoryAnalysisResult(
            predicted_class="unverified",
            confidence=0.0,
            cycle_count=0,
            quality_status=status,
            sample_rate=16000,
            duration_seconds=0.0,
            probabilities={},
            acoustic_embedding_dim=768,
            model_version="SwasthAI-RespLLM-light-v1",
            explanation=explanation,
            respllm_narrative=None,
            human_review_required=True,
        )


respiratory_inference_service = RespiratoryInferenceService()
