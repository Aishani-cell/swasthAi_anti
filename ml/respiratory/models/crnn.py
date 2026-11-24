"""
Compatibility wrapper.

Older modules imported CompactRespiratoryCRNN. The trained respiratory model
is RespLLM in respllm.py. This wrapper exposes the same forward contract
(class probabilities and a 768-d embedding) by running that encoder.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import torch

from ml.respiratory.models.respllm import RESPIRATORY_CLASSES, RespLLM
from ml.respiratory.preprocessing.audio import fit_mel_frames


class CompactRespiratoryCRNN:
    def __init__(self, n_mels: int = 64, n_classes: int = 4, embedding_dim: int = 768, seed: int = 42):
        self.n_mels = n_mels
        self.n_classes = n_classes
        self.embedding_dim = embedding_dim
        torch.manual_seed(seed)
        self.model = RespLLM(n_mels=n_mels, n_classes=n_classes, embed_dim=embedding_dim)
        self.model.eval()

    def forward(self, mel_spec: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        mel = fit_mel_frames(np.asarray(mel_spec, dtype=np.float32), self.model.n_frames)
        if mel.shape[0] != self.n_mels:
            raise ValueError(f"Expected {self.n_mels} mel bins, got {mel.shape[0]}")
        with torch.no_grad():
            logits, embedding = self.model.encode(torch.tensor(mel, dtype=torch.float32).unsqueeze(0))
            probabilities = torch.softmax(logits, dim=-1)[0].cpu().numpy()
            embedding_np = embedding[0].cpu().numpy()
        return probabilities.astype(np.float32), embedding_np.astype(np.float32)

    def save_weights(self, path: str):
        torch.save({"model_state": self.model.state_dict(), "dataset_source": "unspecified"}, path)

    def load_weights(self, path: str):
        blob = torch.load(path, map_location="cpu", weights_only=False)
        state = blob["model_state"] if isinstance(blob, dict) and "model_state" in blob else blob
        self.model.load_state_dict(state)
