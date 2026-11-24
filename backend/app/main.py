"""
SwasthAI FastAPI Application Entry Point
Hardware-Optimized, Privacy-Preserving, Neuro-Symbolic Multimodal CDSS.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db.session import init_db
from backend.app.api.auth import router as auth_router
from backend.app.api.patients import router as patients_router
from backend.app.api.consultations import router as consultations_router
from backend.app.api.ml_routes import router as ml_router
from backend.app.api.dataset_routes import router as dataset_router

# Initialize database tables and seed clinical users
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Hardware-Optimized, Privacy-Preserving, Neuro-Symbolic, Multimodal Clinical Decision "
        "Support System for Rural Primary Healthpods (ITU-T Recommendation Y.4218, Satnavari Village)."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for offline local healthpod use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api/v1
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(patients_router, prefix=settings.API_V1_PREFIX)
app.include_router(consultations_router, prefix=settings.API_V1_PREFIX)
app.include_router(ml_router, prefix=settings.API_V1_PREFIX)
app.include_router(dataset_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "deployment": "Satnavari Healthpod (Offline Capable)",
        "docs": "/docs",
        "health_check": "ALL_SYSTEMS_FUNCTIONAL"
    }
