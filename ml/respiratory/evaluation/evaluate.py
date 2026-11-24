"""
Evaluate a saved RespLLM checkpoint on the patient-disjoint holdout
recorded inside that checkpoint. Does not invent scores when the
checkpoint or its source audio is missing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch

from ml.respiratory.data.icbhi import discover_cycles, find_split_lists, patient_independent_split
from ml.respiratory.evaluation.curves import write_confusion_svg
from ml.respiratory.evaluation.metrics import classification_report
from ml.respiratory.models.respllm import RESPIRATORY_CLASSES, RespLLM
from ml.respiratory.paths import BEST_CHECKPOINT, LATEST_EVAL, REPORT_DIR
from ml.respiratory.preprocessing.audio import cycle_to_log_mel, read_wav_file
from ml.respiratory.runtime import release_torch_memory, torch_device_preference
from ml.respiratory.training.train import generate_synthetic_cycles


def _select_holdout(blob: Dict) -> List[Dict]:
    source = blob.get("dataset_source")
    split = blob.get("split") or {}
    test_patients = set(split.get("test_patients") or [])
    if source == "synthetic_protocol_smoke":
        cycles = generate_synthetic_cycles()
        return [c for c in cycles if c["patient_id"] in test_patients]
    if source == "icbhi2017":
        from ml.respiratory.paths import ICBHI_DIR
        raw = discover_cycles(ICBHI_DIR)
        train_names, test_names = find_split_lists(ICBHI_DIR)
        _, test, _ = patient_independent_split(raw, train_names=train_names, test_names=test_names)
        if test_patients:
            test = [c for c in test if c["patient_id"] in test_patients] or test
        loaded = []
        cache = {}
        for cycle in test:
            if cycle["audio_path"] not in cache:
                cache[cycle["audio_path"]] = read_wav_file(cycle["audio_path"])
            samples, sr = cache[cycle["audio_path"]]
            cycle = dict(cycle)
            cycle["spectrogram"] = cycle_to_log_mel(samples, sr, cycle["start_sec"], cycle["end_sec"])
            loaded.append(cycle)
        return loaded
    return []


def evaluate_respiratory_model(checkpoint_path: str = "") -> Dict:
    path = Path(checkpoint_path) if checkpoint_path else BEST_CHECKPOINT
    if not path.exists():
        result = {
            "status": "NOT_EVALUATED",
            "reason": f"No checkpoint at {path}. Training metrics were not invented.",
        }
        LATEST_EVAL.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    device = torch_device_preference()
    blob = torch.load(path, map_location=device, weights_only=False)
    holdout = _select_holdout(blob)
    if not holdout:
        result = {
            "status": "NOT_EVALUATED",
            "reason": "Checkpoint has no matching holdout audio. ICBHI files may be absent.",
            "dataset_source": blob.get("dataset_source"),
        }
        LATEST_EVAL.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    model = RespLLM()
    model.load_state_dict(blob["model_state"])
    model.to(device)
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for start in range(0, len(holdout), 8):
            batch = holdout[start:start + 8]
            mel = torch.tensor(np.stack([c["spectrogram"] for c in batch]), dtype=torch.float32, device=device)
            logits, _ = model.encode(mel)
            preds = torch.argmax(logits, dim=1).cpu().numpy().tolist()
            y_pred.extend(int(p) for p in preds)
            y_true.extend(int(c["label_idx"]) for c in batch)
    metrics = classification_report(y_true, y_pred, RESPIRATORY_CLASSES)
    write_confusion_svg(metrics["confusion_matrix"], RESPIRATORY_CLASSES, REPORT_DIR / "holdout_confusion_matrix.svg")
    result = {
        "status": "EVALUATED",
        "dataset_source": blob.get("dataset_source"),
        "metrics_are_icbhi": blob.get("dataset_source") == "icbhi2017",
        "checkpoint": str(path),
        "holdout_cycles": len(holdout),
        "device": str(device),
        **metrics,
    }
    LATEST_EVAL.write_text(json.dumps(result, indent=2), encoding="utf-8")
    del model
    release_torch_memory()
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate_respiratory_model(), indent=2))
