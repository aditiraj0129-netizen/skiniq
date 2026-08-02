from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.ml.ocr_agent import extract_raw_text
from app.agents.ingredient_agent import analyze_product_text, summarize_risk

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/scan-label")
async def scan_product_label(
    file: UploadFile = File(...),
    skin_type: str = Query(default=None, description="oily / dry / normal - optional, personalizes the risk summary"),
    db: Session = Depends(get_db),
):
    """
    Upload a photo of a product's ingredient label.
    Pipeline: OCR extracts raw text -> fuzzy substring scan against the
    28k-name gazetteer -> cross-reference with curated risk database ->
    tier assignment by position -> risk summary.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    image_bytes = await file.read()

    try:
        raw_text = extract_raw_text(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text detected in the image. Try a clearer, well-lit photo of the ingredient list.",
        )

    analyzed = analyze_product_text(raw_text, db)
    risk_summary = summarize_risk(analyzed, user_skin_type=skin_type)

    return {
        "raw_ocr_text": raw_text,
        "ingredients": analyzed,
        "risk_summary": risk_summary,
    }
