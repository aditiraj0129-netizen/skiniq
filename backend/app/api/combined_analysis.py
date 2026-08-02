from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.ml.inference import analyze_skin_image
from app.ml.ocr_agent import extract_raw_text
from app.agents.ingredient_agent import analyze_product_text, summarize_risk
from app.agents.coordinator_agent import build_combined_report
from app.models.models import AgentOutputLog

router = APIRouter()
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _check_file(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")


@router.post("/full-report")
async def full_skin_and_product_report(
    face_photo: UploadFile = File(...),
    label_photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    The real multi-agent endpoint: runs the Vision Agent on a face photo AND
    the OCR + Ingredient Agent on a product label photo, then coordinates
    both outputs into one personalized report. Every agent's output is
    logged to the audit trail table.
    """
    _check_file(face_photo)
    _check_file(label_photo)

    face_bytes = await face_photo.read()
    label_bytes = await label_photo.read()

    # --- Vision Agent ---
    try:
        vision_result = analyze_skin_image(face_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision agent failed: {e}")

    db.add(AgentOutputLog(
        agent_name="vision_agent",
        input_summary={"file": face_photo.filename},
        output_summary=vision_result,
        confidence=vision_result.get("skin_type_confidence"),
    ))

    # --- OCR + Ingredient Agent ---
    try:
        raw_text = extract_raw_text(label_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR agent failed: {e}")

    analyzed = analyze_product_text(raw_text, db)
    risk_summary = summarize_risk(analyzed, user_skin_type=vision_result.get("skin_type"))
    ingredient_result = {
        "raw_ocr_text": raw_text,
        "ingredients": analyzed,
        "risk_summary": risk_summary,
    }

    db.add(AgentOutputLog(
        agent_name="ingredient_agent",
        input_summary={"file": label_photo.filename, "ingredients_recognized": len(analyzed)},
        output_summary={"risk_summary": risk_summary},
        confidence=None,
    ))

    # --- Coordinator Agent ---
    combined = build_combined_report(vision_result, ingredient_result)

    db.add(AgentOutputLog(
        agent_name="coordinator_agent",
        input_summary={"note": "cross-referenced vision + ingredient outputs"},
        output_summary=combined["coordinated_insights"],
        confidence=None,
        triggered_debate=combined["coordinated_insights"]["requires_debate"],
    ))

    db.commit()

    return combined