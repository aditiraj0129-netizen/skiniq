from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from app.ml.inference import analyze_skin_image
from app.agents.profile_resolver import resolve_skin_profile

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/analyze")
async def analyze_skin(
    file: UploadFile = File(...),
    tone_category: str = Query(default=None, description="Optional self-report: bright / mid / brown / black. Used only if the model is low-confidence."),
    skin_type_self_report: str = Query(default=None, description="Optional self-report: oily / dry / normal. Used only if the model is low-confidence."),
):
    """
    Upload a face photo, get back a skin analysis with confidence intervals.
    If tone_category or skin_type_self_report are provided AND the model's
    own prediction was low-confidence, the self-report is used instead of
    an uncertain automated guess.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Please upload a JPEG, PNG, or WEBP image.",
        )

    image_bytes = await file.read()

    try:
        model_result = analyze_skin_image(image_bytes)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")

    self_report = None
    if tone_category or skin_type_self_report:
        self_report = {"tone_category": tone_category, "skin_type": skin_type_self_report}

    resolved = resolve_skin_profile(model_result, self_report)
    return resolved