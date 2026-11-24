"""
SwasthAI Configuration Module
Hardware-optimized for Intel Core i5-14450HX, 24GB RAM, RTX 3050 Laptop GPU (6GB VRAM)
"""
import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINTS_DIR = BASE_DIR / "ml" / "respiratory" / "checkpoints"
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "SwasthAI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Storage directories
    UPLOAD_DIR: str = str(DATA_DIR / "uploads")
    
    # Environment
    ENV: str = os.getenv("SWASTHAI_ENV", "development")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "swasthai-secure-key-primary-healthpod-satnavari-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours for healthpod shifts
    
    # Storage & SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/swasthai.db")
    DB_PATH: str = str(BASE_DIR / "swasthai.db")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB limit
    
    # Hardware Adaptation (RTX 3050 6GB VRAM)
    DEVICE: str = "cuda" if os.getenv("DEVICE") == "cuda" else "cpu"
    MAX_ACTIVE_MODELS: int = 1
    MAX_VRAM_ALLOCATION_MB: int = 5000
    
    # LLM Settings
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:3b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ENABLE_DETERMINISTIC_FALLBACK: bool = True
    
    # Safety Engine Thresholds
    RATCLIFF_OBERSHELP_THRESHOLD: float = 0.90
    NEGATION_LOOKAHEAD_CHARS: int = 20
    RAG_DISTANCE_THRESHOLD: float = 0.35  # tau in 1 - sim <= tau
    RAG_TOP_K: int = 3
    
    # Respiratory Acoustics (ICBHI protocol)
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_MEL_BINS: int = 64
    AUDIO_SEGMENT_DURATION_SEC: float = 5.0
    RESPIRATORY_BATCH_SIZE: int = 8
    
settings = Settings()
