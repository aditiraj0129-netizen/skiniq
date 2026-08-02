"""
Advisory Agent: three related but distinct pieces of proactive guidance.

1. Skin-type avoidance list -- BEFORE any product is scanned, tell the user
   what ingredient categories are generally worth avoiding for their skin
   type, computed from our existing curated ingredient risk data.
2. OTC (over-the-counter) suggestions -- general educational info, gated
   behind an explicit user acknowledgment that they'll confirm with a
   dermatologist/pharmacist before using anything. Never shown otherwise.
3. Local community trend -- how many OTHER reports nearby, recently,
   matched a similar symptom category. Honest about small-sample-size
   demo data rather than pretending to have real epidemiological signal.
"""
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.models import Ingredient, SensitiveSymptomReport

# ---------- 1. Skin-type avoidance list ----------

DRYING_AGENT_NAMES = {"Alcohol Denat", "Sodium Lauryl Sulfate", "Witch Hazel"}


def get_avoid_list_for_skin_type(skin_type: str, db: Session) -> dict:
    ingredients = db.query(Ingredient).all()

    if skin_type == "oily":
        flagged = [i for i in ingredients if (i.comedogenic_rating or 0) >= 3]
        reason = "These are comedogenic (pore-clogging) at a level that's often worth avoiding for oily, acne-prone skin."
    elif skin_type == "dry":
        flagged = [i for i in ingredients if i.name in DRYING_AGENT_NAMES]
        reason = "These are common drying/stripping agents that can worsen dryness or barrier damage."
    else:
        flagged = [i for i in ingredients if i.is_common_allergen]
        reason = "These are common allergens/irritants worth being cautious about, regardless of skin type."

    return {
        "skin_type": skin_type,
        "ingredients_to_watch": [i.name for i in flagged],
        "reason": reason,
        "disclaimer": "This is general educational guidance based on common ingredient properties, not a personalized medical recommendation.",
    }


# ---------- 2. OTC suggestions (gated behind explicit acknowledgment) ----------

OTC_SUGGESTIONS = {
    "irritation": "A fragrance-free, gentle moisturizer may help. A short course of OTC 1% hydrocortisone cream is sometimes used for itching/irritation, typically no more than a few days without medical guidance.",
    "allergy": "An OTC oral antihistamine (e.g. cetirizine) is sometimes used for allergic itching. Discontinuing the suspected product is usually the first step.",
    "sun-related": "A broad-spectrum SPF 30+ sunscreen, reapplied regularly, and avoiding peak sun hours (typically 10am-4pm) may help going forward.",
    "infection-signal": "Do not self-treat with OTC products. Signs like pus, spreading redness, fever, or bleeding need prompt medical evaluation.",
}

OTC_CONSENT_DISCLAIMER = (
    "These are general educational suggestions, not a prescription or personalized medical advice. "
    "Please confirm suitability with a dermatologist or pharmacist before using any medication -- "
    "especially if you have allergies, are pregnant/breastfeeding, or take other medications."
)


def get_otc_suggestions(categories: list[str], acknowledged: bool) -> dict:
    if not acknowledged:
        return {
            "shown": False,
            "note": "General OTC suggestions are available -- check the acknowledgment box to view them.",
        }

    suggestions = []
    for cat in set(categories):
        if cat in OTC_SUGGESTIONS:
            suggestions.append({"category": cat, "suggestion": OTC_SUGGESTIONS[cat]})

    return {
        "shown": True,
        "suggestions": suggestions,
        "disclaimer": OTC_CONSENT_DISCLAIMER,
    }


# ---------- 3. Local community trend ----------

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def get_local_trend(lat: float, lng: float, category: str, db: Session, radius_km: float = 25, days: int = 30) -> dict:
    if lat is None or lng is None or not category:
        return {"available": False, "note": "Location not provided -- local trend context unavailable."}

    cutoff = datetime.utcnow() - timedelta(days=days)
    recent_reports = db.query(SensitiveSymptomReport).filter(
        SensitiveSymptomReport.created_at >= cutoff,
        SensitiveSymptomReport.top_category == category,
        SensitiveSymptomReport.latitude.isnot(None),
    ).all()

    nearby_count = sum(
        1 for r in recent_reports
        if haversine_km(lat, lng, r.latitude, r.longitude) <= radius_km
    )

    if nearby_count < 3:
        return {
            "available": True,
            "nearby_similar_reports": nearby_count,
            "note": "Not enough nearby data yet to identify a meaningful local trend -- this grows more useful as more reports come in.",
        }

    return {
        "available": True,
        "nearby_similar_reports": nearby_count,
        "note": f"{nearby_count} other reports of a similar pattern were logged nearby in the last {days} days.",
    }
