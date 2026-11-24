"""Repository paths for respiratory training artifacts."""
from pathlib import Path

RESPIRATORY_DIR = Path(__file__).resolve().parent
ML_DIR = RESPIRATORY_DIR.parent
REPO_ROOT = ML_DIR.parent
CHECKPOINT_DIR = RESPIRATORY_DIR / "checkpoints"
ICBHI_DIR = REPO_ROOT / "data" / "external" / "icbhi"
REPORT_DIR = REPO_ROOT / "reports" / "respiratory"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

BEST_CHECKPOINT = CHECKPOINT_DIR / "best_respllm.pt"
LATEST_METRICS = REPORT_DIR / "latest_training.json"
LATEST_EVAL = REPORT_DIR / "latest_evaluation.json"
