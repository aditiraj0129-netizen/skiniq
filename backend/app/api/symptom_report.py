from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.agents.symptom_agent import analyze_symptoms
from app.agents.advisory_agent import get_avoid_list_for_skin_type, get_otc_suggestions, get_local_trend
from app.models.models import SensitiveSymptomReport

router = APIRouter()


class SymptomReportIn(BaseModel):
    """
    No image field exists here, by design -- this endpoint never accepts a
    photo, so private/sensitive-area concerns can be described safely in
    text only.
    """
    body_area: str
    duration_days: int
    symptoms_text: str
    severity: int  # 1-5
    skin_type: Optional[str] = None   # oily / dry / normal -- enables the proactive avoidance list
    recent_products: Optional[list[str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    acknowledge_otc_disclaimer: bool = False   # must be explicitly true to see OTC suggestions


@router.post("/report")
def submit_symptom_report(report: SymptomReportIn, db: Session = Depends(get_db)):
    """
    Text-only symptom analysis -- no photo required or accepted, so this is
    safe to use for any body area including private/sensitive concerns.
    Also returns: a proactive skin-type avoidance list, gated OTC
    suggestions, and local community trend context.
    """
    analysis = analyze_symptoms(
        symptoms_text=report.symptoms_text,
        severity=report.severity,
        db=db,
        recent_products=report.recent_products,
        lat=report.latitude,
        lng=report.longitude,
    )

    top_category = analysis["possible_causes"][0]["category"] if analysis["possible_causes"] else None
    categories_found = [c["category"] for c in analysis["possible_causes"]]

    avoid_list = None
    if report.skin_type:
        avoid_list = get_avoid_list_for_skin_type(report.skin_type, db)

    otc = get_otc_suggestions(categories_found, report.acknowledge_otc_disclaimer)

    local_trend = get_local_trend(report.latitude, report.longitude, top_category, db)

    db.add(SensitiveSymptomReport(
        body_area=report.body_area,
        duration_days=report.duration_days,
        symptoms_text=report.symptoms_text,
        severity=report.severity,
        top_category=top_category,
        latitude=report.latitude,
        longitude=report.longitude,
    ))
    db.commit()

    analysis["proactive_avoid_list"] = avoid_list
    analysis["otc_suggestions"] = otc
    analysis["local_trend"] = local_trend

    return analysis