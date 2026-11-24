"""
Sequential model runtime.

The RTX 3050 Laptop GPU has 6144 MiB. Vision, respiratory, and language
models are never resident together. Loading one model unloads the previous
one and releases CUDA cache. If CUDA is missing or allocation fails, work
continues on CPU.
"""
from __future__ import annotations

import gc
from typing import Optional

_ACTIVE_NAME: Optional[str] = None


def torch_device_preference():
    import torch
    if torch.cuda.is_available():
        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info()
            # Leave headroom under the 5 GB working cap on a 6 GB card.
            if free_bytes >= 700 * 1024 * 1024 and total_bytes <= 8 * 1024 * 1024 * 1024:
                return torch.device("cuda")
            if free_bytes >= 700 * 1024 * 1024:
                return torch.device("cuda")
        except Exception:
            return torch.device("cuda")
    return torch.device("cpu")


def mark_active(name: Optional[str]) -> None:
    global _ACTIVE_NAME
    _ACTIVE_NAME = name


def active_model() -> Optional[str]:
    return _ACTIVE_NAME


def release_torch_memory() -> None:
    global _ACTIVE_NAME
    _ACTIVE_NAME = None
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def device_report() -> dict:
    report = {"active_model": _ACTIVE_NAME, "cuda_available": False, "device": "cpu"}
    try:
        import torch
        report["torch_version"] = torch.__version__
        report["cuda_build"] = torch.version.cuda
        report["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            report["gpu_name"] = torch.cuda.get_device_name(0)
            free_bytes, total_bytes = torch.cuda.mem_get_info()
            report["vram_free_mib"] = round(free_bytes / (1024 * 1024), 1)
            report["vram_total_mib"] = round(total_bytes / (1024 * 1024), 1)
        report["device"] = str(torch_device_preference())
    except Exception as exc:
        report["torch_error"] = str(exc)
    return report
