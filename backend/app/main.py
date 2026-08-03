"""
SkinIQ backend entrypoint.

Run locally with:  uvicorn app.main:app --reload
Then open:          http://127.0.0.1:8000/docs   (auto-generated interactive API docs)
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.models import models  # noqa: F401  (import so tables register with Base)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkinIQ API",
    description="A trust-first, multi-agent skin health advisor. "
                 "All outputs are recommendations, not medical diagnoses.",
    version="0.1.0",
)

# In production, set FRONTEND_URL to your deployed Netlify URL for tighter CORS.
# Falls back to "*" so local development keeps working without extra config.
allowed_origin = os.getenv("FRONTEND_URL", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin] if allowed_origin != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warm_up_models():
    """
    Loads the vision model and OCR reader once at server boot instead of on
    the first user request -- avoids a slow/timing-out first request in
    production, where cold model loading can take several seconds.
    """
    try:
        from app.ml.inference import get_model
        get_model()
        print("Vision model warmed up.")
    except Exception as e:
        print(f"Vision model warmup skipped/failed: {e}")

    try:
        from app.ml.ocr_agent import get_reader
        get_reader()
        print("OCR reader warmed up.")
    except Exception as e:
        print(f"OCR warmup skipped/failed: {e}")


@app.get("/health")
def health_check():
    """Simple endpoint to confirm the server is alive -- useful for deployment checks."""
    return {"status": "ok", "service": "skiniq-api"}


@app.get("/")
def root():
    return {
        "message": "Welcome to SkinIQ API",
        "docs": "/docs",
        "disclaimer": "This service provides recommendations only, not medical diagnoses.",
    }

from app.api import skin_analysis
app.include_router(skin_analysis.router, prefix="/api/skin", tags=["skin-analysis"])

from app.api import product_scan
app.include_router(product_scan.router, prefix="/api/product", tags=["product-scan"])

from app.api import combined_analysis
app.include_router(combined_analysis.router, prefix="/api/analyze", tags=["multi-agent-analysis"])

from app.api import recommendations
app.include_router(recommendations.router, prefix="/api/recommend", tags=["recommendations"])

from app.api import symptom_report
app.include_router(symptom_report.router, prefix="/api/symptom", tags=["symptom-analysis"])
from app.api import skin_quiz
app.include_router(skin_quiz.router, prefix="/api/skin", tags=["skin-quiz"])

from app.api import chat
app.include_router(chat.router, prefix="/api/chat", tags=["chatbot"])