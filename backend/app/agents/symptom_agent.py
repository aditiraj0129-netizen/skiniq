"""
Symptom Analysis Agent: text-only, by design -- no image parameter exists
anywhere in this pipeline. Cross-references the user's described symptoms
against a keyword knowledge base (fuzzy NLP matching), recent product usage,
and real weather/UV data, then produces an educational (not diagnostic)
report with an honest urgency flag.
"""
from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session

from app.models.models import SymptomKnowledge
from app.ml.weather_agent import get_weather_context, interpret_uv

URGENCY_RANK = {"routine": 0, "prompt": 1, "urgent": 2}
KEYWORD_MATCH_THRESHOLD = 70


def match_symptom_causes(symptoms_text: str, db: Session) -> list[dict]:
    """Fuzzy substring matching against the knowledge base keywords -- same
    technique as the ingredient agent, applied to symptom description text."""
    knowledge = db.query(SymptomKnowledge).all()
    if not knowledge:
        return []

    keyword_map = {k.keyword: k for k in knowledge}
    keywords = list(keyword_map.keys())

    matches = process.extract(
        symptoms_text, keywords, scorer=fuzz.partial_ratio,
        score_cutoff=KEYWORD_MATCH_THRESHOLD, limit=10,
    )

    results = []
    seen_causes = set()
    for keyword, score, _ in matches:
        k = keyword_map[keyword]
        if k.possible_cause in seen_causes:
            continue
        seen_causes.add(k.possible_cause)
        results.append({
            "matched_keyword": keyword,
            "possible_cause": k.possible_cause,
            "category": k.category,
            "urgency": k.urgency,
            "note": k.note,
            "match_confidence": round(score, 1),
        })

    return results


def determine_overall_urgency(matched_causes: list[dict], severity: int) -> str:
    """Takes the highest urgency level found, escalated further if the user
    self-reported high severity -- conservative by design (health-adjacent)."""
    max_urgency = "routine"
    for m in matched_causes:
        if URGENCY_RANK.get(m["urgency"], 0) > URGENCY_RANK.get(max_urgency, 0):
            max_urgency = m["urgency"]

    if severity >= 4 and URGENCY_RANK[max_urgency] < URGENCY_RANK["prompt"]:
        max_urgency = "prompt"

    return max_urgency


def analyze_symptoms(
    symptoms_text: str,
    severity: int,
    db: Session,
    recent_products: list[str] = None,
    lat: float = None,
    lng: float = None,
) -> dict:
    matched_causes = match_symptom_causes(symptoms_text, db)
    urgency = determine_overall_urgency(matched_causes, severity)

    weather_note = None
    if lat is not None and lng is not None:
        weather = get_weather_context(lat, lng)
        if weather["available"]:
            weather_note = interpret_uv(weather["uv_index"])

    product_note = None
    if recent_products:
        product_note = (
            f"You reported recently using: {', '.join(recent_products)}. "
            "If symptoms began after starting one of these, consider pausing "
            "that product and monitoring for improvement."
        )

    urgency_messages = {
        "routine": "This appears to be a common, non-urgent pattern based on your description. Monitor and consider a dermatologist visit if it persists or worsens.",
        "prompt": "Based on your description, we'd recommend seeing a dermatologist soon rather than waiting.",
        "urgent": "Based on your description, please seek medical attention promptly -- this pattern can indicate something needing timely evaluation.",
    }

    return {
        "possible_causes": matched_causes,
        "weather_context_note": weather_note,
        "product_history_note": product_note,
        "urgency_level": urgency,
        "urgency_message": urgency_messages[urgency],
        "disclaimer": (
            "This is an educational, automated analysis based on common patterns -- "
            "it is NOT a diagnosis. Please consult a licensed dermatologist for "
            "an accurate evaluation, especially for anything concerning or persistent."
        ),
    }