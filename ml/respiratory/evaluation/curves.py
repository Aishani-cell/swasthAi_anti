"""Dependency-free SVG training curves and confusion matrices."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence


def write_training_curve(history: dict, path: Path) -> None:
    epochs = history.get("epoch", [])
    train_loss = history.get("train_loss", [])
    val_loss = history.get("val_loss", [])
    val_f1 = history.get("val_macro_f1", [])
    width, height = 640, 360
    pad = 40

    def polyline(values: Sequence[float], color: str) -> str:
        if not values:
            return ""
        lo = min(min(train_loss or [0]), min(val_loss or [0]), 0)
        hi = max(max(train_loss or [1]), max(val_loss or [1]), 1e-6)
        span = max(hi - lo, 1e-6)
        coords = []
        for i, value in enumerate(values):
            x = pad + (width - 2 * pad) * (i / max(1, len(values) - 1))
            y = height - pad - (height - 2 * pad) * ((value - lo) / span)
            coords.append(f"{x:.1f},{y:.1f}")
        return f"<polyline fill='none' stroke='{color}' stroke-width='2' points='{' '.join(coords)}'/>"

    f1_coords = []
    for i, value in enumerate(val_f1):
        x = pad + (width - 2 * pad) * (i / max(1, len(val_f1) - 1))
        y = height - pad - (height - 2 * pad) * value
        f1_coords.append(f"{x:.1f},{y:.1f}")
    f1_line = ""
    if f1_coords:
        f1_line = f"<polyline fill='none' stroke='#2a9d8f' stroke-width='2' stroke-dasharray='4 3' points='{' '.join(f1_coords)}'/>"

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{pad}' y='24' font-family='sans-serif' font-size='16'>RespLLM training curve</text>
{polyline(train_loss, '#1d3557')}
{polyline(val_loss, '#e76f51')}
{f1_line}
<text x='{pad}' y='{height - 8}' font-family='sans-serif' font-size='12'>epochs: {len(epochs)} · navy train loss · coral val loss · dashed val macro-F1</text>
</svg>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def write_confusion_svg(matrix: Sequence[Sequence[int]], class_names: Sequence[str], path: Path) -> None:
    cell = 72
    pad = 90
    n = len(class_names)
    size = pad + cell * n + 20
    peak = max((max(row) if row else 1) for row in matrix) or 1
    rects = []
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            shade = 255 - int(220 * (value / peak))
            x = pad + j * cell
            y = pad + i * cell
            rects.append(
                f"<rect x='{x}' y='{y}' width='{cell - 4}' height='{cell - 4}' fill='rgb({shade},{shade},255)' stroke='#ccc'/>"
                f"<text x='{x + cell / 2}' y='{y + cell / 2}' text-anchor='middle' font-family='sans-serif' font-size='14'>{value}</text>"
            )
    labels = []
    for i, name in enumerate(class_names):
        labels.append(f"<text x='{pad - 8}' y='{pad + i * cell + cell / 2}' text-anchor='end' font-family='sans-serif' font-size='12'>{name}</text>")
        labels.append(f"<text x='{pad + i * cell + cell / 2}' y='{pad - 10}' text-anchor='middle' font-family='sans-serif' font-size='12'>{name}</text>")
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'>
<rect width='100%' height='100%' fill='white'/>
<text x='16' y='24' font-family='sans-serif' font-size='16'>Confusion matrix (rows true, columns predicted)</text>
{''.join(labels)}
{''.join(rects)}
</svg>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
