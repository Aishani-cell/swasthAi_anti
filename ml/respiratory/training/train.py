"""
RespLLM training.

Uses the official ICBHI 2017 cycles when data/external/icbhi contains paired
wav/txt files. Otherwise a smoke run trains on synthetic cycles that follow
the same four labels and the same patient-disjoint split. Synthetic metrics
are stored with dataset_source='synthetic_protocol_smoke' and are not ICBHI
scores.

Checkpoints can be resumed. One model is loaded at a time.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from ml.respiratory.data.icbhi import (
    class_weights_from_labels,
    dataset_status,
    discover_cycles,
    find_split_lists,
    patient_independent_split,
)
from ml.respiratory.evaluation.curves import write_confusion_svg, write_training_curve
from ml.respiratory.evaluation.metrics import classification_report
from ml.respiratory.models.respllm import (
    RESPIRATORY_CLASSES,
    RespLLM,
    caption_tensor,
    classification_and_caption_loss,
    count_parameters,
    respllm_config_dict,
)
from ml.respiratory.paths import BEST_CHECKPOINT, CHECKPOINT_DIR, LATEST_METRICS, REPORT_DIR
from ml.respiratory.preprocessing.audio import (
    compute_log_mel_spectrogram,
    cycle_to_log_mel,
    fit_mel_frames,
    read_wav_file,
)
from ml.respiratory.runtime import mark_active, release_torch_memory, torch_device_preference


def _synthetic_wave(label: str, sr: int, seconds: float, rng: np.random.RandomState) -> np.ndarray:
    t = np.arange(int(sr * seconds), dtype=np.float32) / sr
    noise = rng.randn(t.shape[0]).astype(np.float32) * 0.05
    if label == "normal":
        wave = 0.2 * np.sin(2 * np.pi * 180 * t) + noise
    elif label == "wheeze":
        wave = 0.35 * np.sin(2 * np.pi * 900 * t) + 0.1 * np.sin(2 * np.pi * 180 * t) + noise
    elif label == "crackle":
        wave = 0.15 * np.sin(2 * np.pi * 160 * t) + noise
        bursts = rng.choice(len(t) - 8, size=6, replace=False)
        for b in bursts:
            wave[b:b + 6] += rng.uniform(0.8, 1.4)
    else:
        wave = 0.3 * np.sin(2 * np.pi * 900 * t) + noise
        bursts = rng.choice(len(t) - 8, size=4, replace=False)
        for b in bursts:
            wave[b:b + 6] += 1.0
    return wave.astype(np.float32)


def generate_synthetic_cycles(n_patients: int = 12, cycles_each: int = 4, seed: int = 42) -> List[Dict]:
    """Patient-tagged synthetic cycles. Not the ICBHI corpus."""
    rng = np.random.RandomState(seed)
    cycles = []
    for offset, patient in enumerate(range(101, 101 + n_patients)):
        # Skew toward normal so class weighting is exercised.
        palette = ["normal", "normal", "crackle", "wheeze", "both"]
        for cycle_index in range(cycles_each):
            label = palette[(offset + cycle_index) % len(palette)]
            wave = _synthetic_wave(label, 16000, 1.2, rng)
            mel = fit_mel_frames(compute_log_mel_spectrogram(wave, sr=16000, n_mels=64), 128)
            cycles.append({
                "patient_id": str(patient),
                "recording_name": f"{patient}_synth.wav",
                "cycle_index": cycle_index,
                "label_name": label,
                "label_idx": RESPIRATORY_CLASSES.index(label),
                "spectrogram": mel,
                "source": "synthetic",
            })
    return cycles


def _load_icbhi_cycles(root: Path) -> List[Dict]:
    raw = discover_cycles(root)
    loaded = []
    cache: Dict[str, tuple] = {}
    for cycle in raw:
        path = cycle["audio_path"]
        if path not in cache:
            cache[path] = read_wav_file(path)
        samples, sr = cache[path]
        mel = cycle_to_log_mel(samples, sr, cycle["start_sec"], cycle["end_sec"])
        loaded.append({**cycle, "spectrogram": mel, "source": "icbhi2017"})
    return loaded


def _batches(indices: Sequence[int], batch_size: int, rng: np.random.RandomState):
    order = np.array(indices)
    rng.shuffle(order)
    for start in range(0, len(order), batch_size):
        yield order[start:start + batch_size]


def train_respiratory_model(
    epochs: int = 5,
    lr: float = 1e-3,
    checkpoint_dir: str = "",
    smoke_test: bool = False,
    data_dir: str = "",
    batch_size: int = 8,
    resume: bool = True,
) -> Dict:
    """
    Train RespLLM. smoke_test=True forces the synthetic protocol even if ICBHI
    is present, so a laptop check cannot be mistaken for a dataset run.
    smoke_test=False trains on ICBHI when the files are installed and refuses
    to invent scores when they are not.
    """
    import torch

    release_torch_memory()
    mark_active("respllm_training")
    out_dir = Path(checkpoint_dir) if checkpoint_dir else CHECKPOINT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir = REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    icbhi_root = Path(data_dir) if data_dir else Path(os.environ.get("SWASTHAI_ICBHI_DIR", ""))
    if not data_dir and not os.environ.get("SWASTHAI_ICBHI_DIR"):
        from ml.respiratory.paths import ICBHI_DIR
        icbhi_root = ICBHI_DIR

    status = dataset_status(icbhi_root)
    use_icbhi = (not smoke_test) and status["present"]
    if not smoke_test and not status["present"]:
        release_torch_memory()
        blocked = {
            "status": "DATASET_MISSING",
            "smoke_test": False,
            "dataset_source": None,
            "metrics_are_icbhi": False,
            "message": (
                "Official ICBHI 2017 audio is not in data/external/icbhi. "
                "No training metrics were produced. See docs/ICBHI_SETUP.md."
            ),
            "dataset_status": status,
        }
        (REPORT_DIR / "dataset_status.json").write_text(json.dumps(blocked, indent=2), encoding="utf-8")
        return blocked

    if use_icbhi:
        cycles = _load_icbhi_cycles(icbhi_root)
        train_names, test_names = find_split_lists(icbhi_root)
        train_set, val_set, split_meta = patient_independent_split(
            cycles, test_ratio=0.4, train_names=train_names, test_names=test_names
        )
        dataset_source = "icbhi2017"
    else:
        cycles = generate_synthetic_cycles()
        train_set, val_set, split_meta = patient_independent_split(cycles, test_ratio=0.4, seed=42)
        dataset_source = "synthetic_protocol_smoke"

    device = torch_device_preference()
    model = RespLLM().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    start_epoch = 1
    best_f1 = -1.0
    history = {"epoch": [], "train_loss": [], "val_loss": [], "val_accuracy": [], "val_macro_f1": []}
    ckpt_path = out_dir / "best_respllm.pt"

    if resume and ckpt_path.exists():
        previous = torch.load(ckpt_path, map_location=device, weights_only=False)
        if previous.get("dataset_source") == dataset_source and "model_state" in previous:
            model.load_state_dict(previous["model_state"])
            if "optimizer_state" in previous:
                optimizer.load_state_dict(previous["optimizer_state"])
            start_epoch = int(previous.get("epoch", 0)) + 1
            best_f1 = float(previous.get("best_macro_f1", -1.0))
            history = previous.get("history", history)

    weights = class_weights_from_labels([c["label_idx"] for c in train_set])
    class_weights = torch.tensor(weights, dtype=torch.float32, device=device)
    rng = np.random.RandomState(42)
    used_cpu_fallback = False

    def run_epoch(trainable: bool):
        nonlocal device, model, optimizer, class_weights, used_cpu_fallback
        model.train(mode=trainable)
        subset = train_set if trainable else val_set
        total_loss = 0.0
        y_true, y_pred = [], []
        indices = list(range(len(subset)))
        batches = _batches(indices, batch_size, rng) if trainable else (
            indices[s:s + batch_size] for s in range(0, len(indices), batch_size)
        )
        context = torch.enable_grad() if trainable else torch.no_grad()
        with context:
            for batch_ids in batches:
                mels = np.stack([subset[int(i)]["spectrogram"] for i in batch_ids])
                labels = [subset[int(i)]["label_name"] for i in batch_ids]
                targets = torch.tensor([subset[int(i)]["label_idx"] for i in batch_ids], dtype=torch.long, device=device)
                mel_tensor = torch.tensor(mels, dtype=torch.float32, device=device)
                tokens = caption_tensor(labels, device)
                try:
                    if trainable:
                        optimizer.zero_grad(set_to_none=True)
                    outputs = model(mel_tensor, tokens)
                    loss = classification_and_caption_loss(outputs, targets, tokens, class_weights if trainable else None)
                    if trainable:
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        optimizer.step()
                except RuntimeError as exc:
                    if "out of memory" not in str(exc).lower() or device.type != "cuda":
                        raise
                    used_cpu_fallback = True
                    torch.cuda.empty_cache()
                    device = torch.device("cpu")
                    model.to(device)
                    class_weights = class_weights.cpu()
                    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
                    continue
                total_loss += float(loss.detach().cpu()) * len(batch_ids)
                preds = torch.argmax(outputs["logits"], dim=1).detach().cpu().numpy().tolist()
                y_true.extend(int(v) for v in targets.detach().cpu().numpy().tolist())
                y_pred.extend(int(v) for v in preds)
        denom = max(1, len(subset))
        return total_loss / denom, y_true, y_pred

    epochs_run = 0
    for epoch in range(start_epoch, start_epoch + epochs):
        train_loss, _, _ = run_epoch(True)
        val_loss, y_true, y_pred = run_epoch(False)
        metrics = classification_report(y_true, y_pred, RESPIRATORY_CLASSES)
        history["epoch"].append(epoch)
        history["train_loss"].append(round(train_loss, 4))
        history["val_loss"].append(round(val_loss, 4))
        history["val_accuracy"].append(metrics["accuracy"])
        history["val_macro_f1"].append(metrics["macro_f1"])
        epochs_run += 1
        if metrics["macro_f1"] >= best_f1:
            best_f1 = metrics["macro_f1"]
            torch.save({
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "config": respllm_config_dict(model),
                "epoch": epoch,
                "best_macro_f1": best_f1,
                "dataset_source": dataset_source,
                "split": split_meta,
                "history": history,
                "class_names": RESPIRATORY_CLASSES,
                "parameter_count": count_parameters(model),
                "device": str(device),
            }, ckpt_path)

    model.eval()
    _, y_true, y_pred = run_epoch(False)
    final_metrics = classification_report(y_true, y_pred, RESPIRATORY_CLASSES)
    if out_dir.resolve() == CHECKPOINT_DIR.resolve():
        write_training_curve(history, report_dir / "training_curve.svg")
        write_confusion_svg(final_metrics["confusion_matrix"], RESPIRATORY_CLASSES, report_dir / "confusion_matrix.svg")

    summary = {
        "status": "COMPLETED",
        "architecture": "RespLLM CNN-BiGRU + closed-vocabulary GRU decoder",
        "parameter_count": count_parameters(model),
        "dataset_source": dataset_source,
        "metrics_are_icbhi": dataset_source == "icbhi2017",
        "smoke_test": smoke_test or dataset_source != "icbhi2017",
        "epochs_requested": epochs,
        "epochs_run": epochs_run,
        "learning_rate": lr,
        "batch_size": batch_size,
        "device": str(device),
        "cpu_fallback_used": used_cpu_fallback,
        "checkpoint_file": str(ckpt_path),
        "train_cycles": len(train_set),
        "val_cycles": len(val_set),
        "class_weights": [round(float(w), 4) for w in weights],
        "split": split_meta,
        "final_metrics": final_metrics,
        "history": history,
        "dataset_status": status,
    }
    if out_dir.resolve() == CHECKPOINT_DIR.resolve():
        LATEST_METRICS.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (report_dir / "experiment_log.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    else:
        (out_dir / "training_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    release_torch_memory()
    return summary


if __name__ == "__main__":
    result = train_respiratory_model(epochs=3, smoke_test=True)
    print(json.dumps({k: result[k] for k in ("status", "dataset_source", "device", "final_metrics") if k in result}, indent=2))
