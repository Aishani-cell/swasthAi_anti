"""
RespLLM — lightweight respiratory audio encoder and closed-vocabulary language head.

The SwasthAI paper (Section 3.4) feeds a 768-dimensional acoustic embedding from
a frozen OPERA-CT model into the evidence graph, and Section 6 lists RespLLM
integration as the lung-sound diagnosis extension. OPERA-CT weights are not
bundled: a 768-d foundation model does not fit a practical offline download on
this laptop, and the published paper does not specify RespLLM layer sizes.

This module is the on-device RespLLM used by SwasthAI:

- CNN + bidirectional GRU acoustic encoder
- attention pooling to a 768-d embedding (OPERA-CT interface width)
- 4-way ICBHI head: normal, crackle, wheeze, both
- GRU language decoder over a closed clinical token vocabulary

The decoder cannot emit drug names, doses, or diagnoses outside that vocabulary.
Outputs are cycle-level acoustic descriptions and always require clinician review.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

RESPIRATORY_CLASSES = ["normal", "crackle", "wheeze", "both"]

# Closed vocabulary. Token order is stable and stored in checkpoints.
RESPLLM_VOCAB: List[str] = [
    "<pad>",
    "<bos>",
    "<eos>",
    "cycle",
    "label",
    "normal",
    "crackle",
    "wheeze",
    "both",
    "discontinuous",
    "continuous",
    "explosive",
    "musical",
    "broadband",
    "low_energy",
    "mixed",
    "review_required",
    "not_a_diagnosis",
]
VOCAB_INDEX = {tok: i for i, tok in enumerate(RESPLLM_VOCAB)}
PAD_ID = VOCAB_INDEX["<pad>"]
BOS_ID = VOCAB_INDEX["<bos>"]
EOS_ID = VOCAB_INDEX["<eos>"]

CLASS_CAPTIONS: Dict[str, List[str]] = {
    "normal": ["<bos>", "cycle", "label", "normal", "broadband", "low_energy", "review_required", "not_a_diagnosis", "<eos>"],
    "crackle": ["<bos>", "cycle", "label", "crackle", "discontinuous", "explosive", "review_required", "not_a_diagnosis", "<eos>"],
    "wheeze": ["<bos>", "cycle", "label", "wheeze", "continuous", "musical", "review_required", "not_a_diagnosis", "<eos>"],
    "both": ["<bos>", "cycle", "label", "both", "discontinuous", "continuous", "mixed", "review_required", "not_a_diagnosis", "<eos>"],
}

TOKEN_TEXT = {
    "cycle": "Respiratory cycle.",
    "label": "Acoustic label",
    "normal": "normal (no adventitious sound pattern).",
    "crackle": "crackle.",
    "wheeze": "wheeze.",
    "both": "both crackle and wheeze.",
    "discontinuous": "Pattern is discontinuous.",
    "continuous": "Pattern is continuous.",
    "explosive": "Short explosive bursts are present.",
    "musical": "A musical narrow-band pattern is present.",
    "broadband": "Energy is broadband.",
    "low_energy": "Adventitious energy is low.",
    "mixed": "Discontinuous and continuous patterns co-occur.",
    "review_required": "Clinician review is required.",
    "not_a_diagnosis": "This is an acoustic description, not a diagnosis or a drug recommendation.",
}


def caption_tensor(labels: List[str], device: torch.device) -> torch.Tensor:
    rows = []
    width = max(len(CLASS_CAPTIONS[name]) for name in RESPIRATORY_CLASSES)
    for name in labels:
        ids = [VOCAB_INDEX[tok] for tok in CLASS_CAPTIONS[name]]
        ids = ids + [PAD_ID] * (width - len(ids))
        rows.append(ids)
    return torch.tensor(rows, dtype=torch.long, device=device)


def tokens_to_narrative(token_ids: List[int]) -> str:
    words = []
    for idx in token_ids:
        if idx < 0 or idx >= len(RESPLLM_VOCAB):
            continue
        tok = RESPLLM_VOCAB[idx]
        if tok in ("<pad>", "<bos>", "<eos>"):
            if tok == "<eos>":
                break
            continue
        words.append(TOKEN_TEXT.get(tok, tok))
    return " ".join(words).strip()


class RespLLM(nn.Module):
    """CNN–BiGRU encoder, 768-d embedding, 4-class head, and closed-vocab GRU decoder."""

    def __init__(
        self,
        n_mels: int = 64,
        n_frames: int = 128,
        n_classes: int = 4,
        embed_dim: int = 768,
        conv_channels: int = 32,
        gru_hidden: int = 64,
        vocab_size: int = len(RESPLLM_VOCAB),
        token_dim: int = 32,
    ):
        super().__init__()
        self.n_mels = n_mels
        self.n_frames = n_frames
        self.n_classes = n_classes
        self.embed_dim = embed_dim
        self.gru_hidden = gru_hidden
        self.vocab_size = vocab_size

        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(4, 16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 2)),
            nn.Conv2d(16, conv_channels, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(8, conv_channels),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 2)),
        )
        self.temporal = nn.GRU(
            input_size=conv_channels,
            hidden_size=gru_hidden,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        temporal_dim = gru_hidden * 2
        self.attention = nn.Linear(temporal_dim, 1)
        self.embed = nn.Linear(temporal_dim, embed_dim)
        self.classifier = nn.Linear(embed_dim, n_classes)

        self.token_embed = nn.Embedding(vocab_size, token_dim, padding_idx=PAD_ID)
        self.acoustic_to_token = nn.Linear(embed_dim, token_dim)
        self.decoder = nn.GRUCell(token_dim * 2, gru_hidden)
        self.decoder_init = nn.Linear(embed_dim, gru_hidden)
        self.lm_head = nn.Linear(gru_hidden, vocab_size)

    def encode(self, mel: torch.Tensor):
        """
        mel: (B, 1, n_mels, n_frames) or (B, n_mels, n_frames)
        returns class logits (B, 4) and embedding (B, 768)
        """
        if mel.dim() == 3:
            mel = mel.unsqueeze(1)
        features = self.encoder(mel)
        # Pool the mel axis. Time stays as the recurrent sequence.
        features = features.mean(dim=2).transpose(1, 2)
        sequence, _ = self.temporal(features)
        weights = torch.softmax(self.attention(sequence).squeeze(-1), dim=1)
        pooled = torch.sum(sequence * weights.unsqueeze(-1), dim=1)
        embedding = torch.tanh(self.embed(pooled))
        logits = self.classifier(embedding)
        return logits, embedding

    def decode_teacher(self, embedding: torch.Tensor, tokens: torch.Tensor) -> torch.Tensor:
        """Teacher-forced next-token logits. tokens: (B, T) including BOS."""
        hidden = torch.tanh(self.decoder_init(embedding))
        acoustic = self.acoustic_to_token(embedding)
        outputs = []
        steps = tokens.size(1) - 1
        for step in range(steps):
            token_vec = self.token_embed(tokens[:, step])
            hidden = self.decoder(torch.cat([token_vec, acoustic], dim=-1), hidden)
            outputs.append(self.lm_head(hidden))
        return torch.stack(outputs, dim=1)

    def generate(self, embedding: torch.Tensor, max_len: int = 16) -> torch.Tensor:
        """Greedy decode. Returns token ids (B, L) including BOS, stopping at EOS."""
        batch = embedding.size(0)
        hidden = torch.tanh(self.decoder_init(embedding))
        acoustic = self.acoustic_to_token(embedding)
        tokens = torch.full((batch, 1), BOS_ID, dtype=torch.long, device=embedding.device)
        finished = torch.zeros(batch, dtype=torch.bool, device=embedding.device)
        for _ in range(max_len):
            token_vec = self.token_embed(tokens[:, -1])
            hidden = self.decoder(torch.cat([token_vec, acoustic], dim=-1), hidden)
            nxt = torch.argmax(self.lm_head(hidden), dim=-1)
            nxt = torch.where(finished, torch.full_like(nxt, PAD_ID), nxt)
            tokens = torch.cat([tokens, nxt.unsqueeze(1)], dim=1)
            finished = finished | (nxt == EOS_ID)
            if bool(finished.all()):
                break
        return tokens

    def forward(self, mel: torch.Tensor, target_tokens: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        logits, embedding = self.encode(mel)
        result = {"logits": logits, "embedding": embedding}
        if target_tokens is not None:
            result["token_logits"] = self.decode_teacher(embedding, target_tokens)
        return result


def respllm_config_dict(model: RespLLM) -> Dict[str, int]:
    return {
        "n_mels": model.n_mels,
        "n_frames": model.n_frames,
        "n_classes": model.n_classes,
        "embed_dim": model.embed_dim,
        "gru_hidden": model.gru_hidden,
        "vocab_size": model.vocab_size,
    }


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def classification_and_caption_loss(
    outputs: Dict[str, torch.Tensor],
    class_targets: torch.Tensor,
    token_targets: torch.Tensor,
    class_weights: Optional[torch.Tensor] = None,
    caption_weight: float = 0.35,
) -> torch.Tensor:
    class_loss = F.cross_entropy(outputs["logits"], class_targets, weight=class_weights)
    token_logits = outputs["token_logits"]
    caption_loss = F.cross_entropy(
        token_logits.reshape(-1, token_logits.size(-1)),
        token_targets[:, 1:].reshape(-1),
        ignore_index=PAD_ID,
    )
    return class_loss + caption_weight * caption_loss
