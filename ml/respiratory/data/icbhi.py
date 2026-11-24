"""
ICBHI 2017 respiratory-cycle dataset reader.

Official distribution (registration required):
https://bhichallenge.med.auth.gr/ICBHI_2017_Challenge

Expected layout after extraction (either the nested or flat form is accepted):

    data/external/icbhi/
      ICBHI_final_database/   # or audio files directly in the root
        101_1b1_Al_sc_Meditron.wav
        101_1b1_Al_sc_Meditron.txt
      filename_train.txt      # optional official lists, one filename per line
      filename_test.txt

Annotation rows are: start_sec end_sec crackle wheeze
with crackle/wheeze in {0, 1}. Patient id is the leading integer of the filename.
Train and test splits are patient-disjoint. Official lists are used when present.
Otherwise a deterministic 60/40 patient split is written into the training report
and labeled unofficial.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from ml.respiratory.models.respllm import RESPIRATORY_CLASSES
from ml.respiratory.paths import ICBHI_DIR

CLASS_TO_INDEX = {name: i for i, name in enumerate(RESPIRATORY_CLASSES)}


def cycle_label(crackle: int, wheeze: int) -> str:
    if crackle and wheeze:
        return "both"
    if crackle:
        return "crackle"
    if wheeze:
        return "wheeze"
    return "normal"


def patient_id_from_filename(name: str) -> str:
    stem = Path(name).stem
    head = stem.split("_", 1)[0]
    digits = "".join(ch for ch in head if ch.isdigit())
    if not digits:
        raise ValueError(f"Cannot read an ICBHI patient id from '{name}'")
    return digits


def parse_annotation_file(path: Path) -> List[Dict[str, float]]:
    cycles = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace(",", " ").split()
        if len(parts) < 4:
            continue
        try:
            start, end = float(parts[0]), float(parts[1])
            crackle, wheeze = int(float(parts[2])), int(float(parts[3]))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_no} is not an ICBHI annotation row") from exc
        if end <= start:
            continue
        label = cycle_label(1 if crackle else 0, 1 if wheeze else 0)
        cycles.append({
            "start_sec": start,
            "end_sec": end,
            "crackle": int(crackle),
            "wheeze": int(wheeze),
            "label_name": label,
            "label_idx": CLASS_TO_INDEX[label],
        })
    return cycles


def _audio_files(root: Path) -> List[Path]:
    files = []
    for pattern in ("*.wav", "*.WAV"):
        files.extend(root.rglob(pattern))
    return sorted(set(files))


def _read_name_list(path: Path) -> set:
    names = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.add(Path(line.split()[0]).name.lower())
    return names


def find_split_lists(root: Path) -> Tuple[Optional[set], Optional[set]]:
    train_names = None
    test_names = None
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        lowered = candidate.name.lower()
        if lowered in {"filename_train.txt", "train_filenames.txt", "icbhi_challenge_train.txt"}:
            train_names = _read_name_list(candidate)
        elif lowered in {"filename_test.txt", "test_filenames.txt", "icbhi_challenge_test.txt"}:
            test_names = _read_name_list(candidate)
    return train_names, test_names


def discover_cycles(root: Path = ICBHI_DIR) -> List[Dict]:
    """Pair each wav with its annotation and expand respiratory cycles."""
    root = Path(root)
    if not root.exists():
        return []
    cycles = []
    for wav_path in _audio_files(root):
        txt_path = wav_path.with_suffix(".txt")
        if not txt_path.exists():
            continue
        patient_id = patient_id_from_filename(wav_path.name)
        for index, cycle in enumerate(parse_annotation_file(txt_path)):
            cycles.append({
                **cycle,
                "patient_id": patient_id,
                "audio_path": str(wav_path),
                "annotation_path": str(txt_path),
                "recording_name": wav_path.name,
                "cycle_index": index,
            })
    return cycles


def patient_independent_split(
    cycles: Sequence[Dict],
    test_ratio: float = 0.4,
    seed: int = 2017,
    train_names: Optional[Iterable[str]] = None,
    test_names: Optional[Iterable[str]] = None,
) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Split cycles so no patient id appears in both sides.
    Official filename lists win when both are provided.
    """
    if train_names and test_names:
        train_set = {name.lower() for name in train_names}
        test_set = {name.lower() for name in test_names}
        train = [c for c in cycles if c["recording_name"].lower() in train_set]
        test = [c for c in cycles if c["recording_name"].lower() in test_set]
        source = "official_filename_lists"
    else:
        patients = sorted({c["patient_id"] for c in cycles})
        rng = np.random.RandomState(seed)
        order = list(patients)
        rng.shuffle(order)
        n_test = max(1, int(round(len(order) * test_ratio))) if len(order) > 1 else 0
        test_patients = set(order[:n_test])
        train = [c for c in cycles if c["patient_id"] not in test_patients]
        test = [c for c in cycles if c["patient_id"] in test_patients]
        source = "patient_shuffle_60_40_unofficial"

    train_patients = {c["patient_id"] for c in train}
    test_patients = {c["patient_id"] for c in test}
    overlap = train_patients & test_patients
    if overlap:
        raise RuntimeError(f"Patient leakage in respiratory split: {sorted(overlap)}")
    meta = {
        "split_source": source,
        "train_patients": sorted(train_patients),
        "test_patients": sorted(test_patients),
        "train_cycles": len(train),
        "test_cycles": len(test),
        "train_label_counts": dict(Counter(c["label_name"] for c in train)),
        "test_label_counts": dict(Counter(c["label_name"] for c in test)),
    }
    return train, test, meta


def class_weights_from_labels(labels: Sequence[int], n_classes: int = 4) -> np.ndarray:
    """Inverse-frequency weights, normalized to mean 1. Empty classes get weight 0."""
    counts = np.bincount(np.asarray(labels, dtype=int), minlength=n_classes).astype(np.float64)
    weights = np.zeros(n_classes, dtype=np.float64)
    present = counts > 0
    weights[present] = counts.sum() / (present.sum() * counts[present])
    return weights.astype(np.float32)


def dataset_status(root: Path = ICBHI_DIR) -> Dict:
    root = Path(root)
    cycles = discover_cycles(root) if root.exists() else []
    train_names, test_names = find_split_lists(root) if root.exists() else (None, None)
    return {
        "path": str(root),
        "present": root.exists() and len(cycles) > 0,
        "recordings": len({c["recording_name"] for c in cycles}),
        "cycles": len(cycles),
        "patients": len({c["patient_id"] for c in cycles}),
        "official_split_lists": bool(train_names and test_names),
        "label_counts": dict(Counter(c["label_name"] for c in cycles)),
    }


def write_cycle_manifest(cycles: Sequence[Dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["patient_id", "recording_name", "cycle_index", "start_sec", "end_sec", "label_name"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for cycle in cycles:
            writer.writerow({key: cycle[key] for key in fields})
