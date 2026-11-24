"""Multiclass accuracy, precision, recall, F1, sensitivity, specificity, and confusion matrix."""
from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np


def confusion_matrix(y_true: Sequence[int], y_pred: Sequence[int], n_classes: int) -> np.ndarray:
    matrix = np.zeros((n_classes, n_classes), dtype=int)
    for truth, pred in zip(y_true, y_pred):
        matrix[int(truth), int(pred)] += 1
    return matrix


def classification_report(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    class_names: Sequence[str],
) -> Dict:
    y_true = [int(v) for v in y_true]
    y_pred = [int(v) for v in y_pred]
    n_classes = len(class_names)
    matrix = confusion_matrix(y_true, y_pred, n_classes)
    per_class = {}
    precisions, recalls, f1s, specificities = [], [], [], []
    for index, name in enumerate(class_names):
        tp = int(matrix[index, index])
        fn = int(matrix[index, :].sum() - tp)
        fp = int(matrix[:, index].sum() - tp)
        tn = int(matrix.sum() - (tp + fn + fp))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        specificity = tn / (tn + fp) if (tn + fp) else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        specificities.append(specificity)
        per_class[name] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "sensitivity": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1": round(f1, 4),
            "support": int(matrix[index, :].sum()),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }
    total = len(y_true)
    accuracy = float(np.trace(matrix) / total) if total else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(float(np.mean(precisions)) if precisions else 0.0, 4),
        "macro_recall": round(float(np.mean(recalls)) if recalls else 0.0, 4),
        "macro_sensitivity": round(float(np.mean(recalls)) if recalls else 0.0, 4),
        "macro_specificity": round(float(np.mean(specificities)) if specificities else 0.0, 4),
        "macro_f1": round(float(np.mean(f1s)) if f1s else 0.0, 4),
        "support": total,
        "confusion_matrix": matrix.tolist(),
        "class_names": list(class_names),
        "per_class": per_class,
    }
