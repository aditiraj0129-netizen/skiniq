"""
Ingredient Matching Agent v2.

Old approach: split OCR text by commas, match each whole chunk exactly.
Problem: messy OCR merges/garbles text, so one bad chunk = total miss,
even when a real ingredient name is sitting right inside it.

New approach: scan the ENTIRE raw OCR text for known ingredient names using
fuzzy substring search (rapidfuzz partial_ratio) against our ~28k-name
gazetteer. This finds ingredient names correctly even when surrounded by
garbled text, because partial_ratio looks for the best-aligned substring
match rather than requiring the whole segment to match cleanly.

Each detected ingredient is then cross-referenced against our curated risk
database. If we have risk data, we return it. If not, we're honest about
that instead of pretending -- "recognized ingredient, risk data not yet
available" is a real, trustworthy answer.
"""
from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session
import re

from app.models.models import Ingredient, KnownIngredientName

RECOGNITION_THRESHOLD = 88
RISK_MATCH_THRESHOLD = 80


def isolate_ingredients_section(raw_text: str) -> str:
    """
    Restricts scanning to the actual ingredients list when we can find the
    'INGREDIENTS:' marker, so marketing copy (e.g. 'Enriched with Shea
    Butter') doesn't get mistaken for the literal ingredient list. Falls
    back to the full text if no marker is found -- better to over-scan
    than to miss everything on an unusually formatted label.
    """
    match = re.search(r"(?i)ingredients\s*:", raw_text)
    if match:
        return raw_text[match.end():]
    return raw_text


def scan_for_ingredients(raw_text: str, db: Session, max_matches: int = 40) -> list[dict]:
    scan_text = isolate_ingredients_section(raw_text)
    gazetteer = [r.name for r in db.query(KnownIngredientName.name).all()]
    if not gazetteer:
        return []

    scored = process.extract(
        scan_text, gazetteer, scorer=fuzz.partial_ratio,
        score_cutoff=RECOGNITION_THRESHOLD, limit=max_matches,
    )

    detected = []
    seen_spans = []
    scored_sorted = sorted(scored, key=lambda x: -len(x[0]))
    for name, score, _ in scored_sorted:
        if any(name.lower() in longer.lower() for longer in seen_spans):
            continue
        seen_spans.append(name)
        detected.append({"name": name, "recognition_confidence": round(score, 1)})

    return detected


def enrich_with_risk_data(detected: list[dict], db: Session) -> list[dict]:
    risk_ingredients = db.query(Ingredient).all()
    if not risk_ingredients:
        for d in detected:
            d.update({"has_risk_data": False, "note": "Risk database not seeded yet."})
        return detected

    risk_names = {ing.name: ing for ing in risk_ingredients}
    choices = list(risk_names.keys())

    for d in detected:
        match = process.extractOne(d["name"], choices, scorer=fuzz.WRatio)
        if match and match[1] >= RISK_MATCH_THRESHOLD:
            ing = risk_names[match[0]]
            d.update({
                "has_risk_data": True,
                "matched_ingredient": ing.name,
                "comedogenic_rating": ing.comedogenic_rating,
                "is_common_allergen": ing.is_common_allergen,
                "purpose": ing.purpose,
            })
        else:
            d.update({
                "has_risk_data": False,
                "note": "Recognized as a real cosmetic ingredient, but detailed "
                        "safety/comedogenic data isn't in our curated database yet.",
            })

    return detected


def assign_tiers_by_appearance_order(raw_text: str, detected: list[dict]) -> list[dict]:
    positions = []
    for d in detected:
        idx = raw_text.lower().find(d["name"].lower())
        positions.append((idx if idx >= 0 else len(raw_text), d))

    positions.sort(key=lambda x: x[0])
    total = len(positions)
    for rank, (_, d) in enumerate(positions):
        fraction = rank / max(total - 1, 1)
        if fraction <= 0.3:
            d["estimated_tier"] = "primary"
        elif fraction <= 0.7:
            d["estimated_tier"] = "moderate"
        else:
            d["estimated_tier"] = "trace"

    return detected


def deduplicate_by_risk_match(detected: list[dict]) -> list[dict]:
    """
    The gazetteer has many near-variant names for the same real ingredient
    (e.g. 'Glyceryl Stearate Citrate', 'Glyceryl Stearate Lactate' both being
    salt variants). Once we know what curated risk ingredient each maps to,
    collapse duplicates into one clean entry -- keeps output demo-ready.
    """
    seen_risk_names = {}
    unmatched = []

    for d in detected:
        key = d.get("matched_ingredient")
        if key:
            if key not in seen_risk_names or d["recognition_confidence"] > seen_risk_names[key]["recognition_confidence"]:
                seen_risk_names[key] = d
        else:
            unmatched.append(d)

    return list(seen_risk_names.values()) + unmatched


def analyze_product_text(raw_text: str, db: Session) -> list[dict]:
    detected = scan_for_ingredients(raw_text, db)
    detected = enrich_with_risk_data(detected, db)
    detected = deduplicate_by_risk_match(detected)
    detected = assign_tiers_by_appearance_order(raw_text, detected)
    return detected


def summarize_risk(analyzed: list[dict], user_skin_type: str = None) -> dict:
    high_comedogenic = [
        d for d in analyzed
        if d.get("has_risk_data") and (d.get("comedogenic_rating") or 0) >= 3
        and d.get("estimated_tier") in ("primary", "moderate")
    ]
    allergens = [d for d in analyzed if d.get("has_risk_data") and d.get("is_common_allergen")]

    flags = []
    if high_comedogenic:
        names = ", ".join(d["matched_ingredient"] for d in high_comedogenic)
        flags.append(f"Contains pore-clogging ingredients at meaningful concentration: {names}.")
    if allergens:
        names = ", ".join(d["matched_ingredient"] for d in allergens)
        flags.append(f"Contains common allergens/irritants: {names}.")
    if user_skin_type == "oily" and high_comedogenic:
        flags.append("These comedogenic ingredients may be especially worth watching for oily skin types.")

    return {
        "flags": flags,
        "flag_count": len(flags),
        "ingredients_recognized": len(analyzed),
        "ingredients_with_risk_data": len([d for d in analyzed if d.get("has_risk_data")]),
        "disclaimer": (
            "This is an automated ingredient analysis based on label text and "
            "a reference database. It is not a clinical assessment -- patch-test "
            "new products and consult a dermatologist for persistent reactions."
        ),
    }