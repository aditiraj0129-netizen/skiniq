"""
Profile Resolver: decides, per field, whether to trust the model's prediction
or fall back to the user's self-report -- based on the model's own confidence.
This is the same "don't guess when unsure" principle as the coordinator agent,
applied at the input level instead of the output level.
"""

TONE_CATEGORY_TO_RANGE = {
    "bright": (1, 2),
    "mid": (3, 4),
    "brown": (4, 5),
    "black": (5, 6),
}

TYPE_CONFIDENCE_THRESHOLD = 0.5
TONE_INTERVAL_WIDTH_THRESHOLD = 2.5


def resolve_skin_profile(model_result: dict, self_report: dict | None) -> dict:
    """
    Returns a resolved profile with a `source` tag per field, so the final
    report is always transparent about whether a value came from the model
    or from the user.
    """
    resolved = dict(model_result)
    resolved["tone_source"] = "model"
    resolved["type_source"] = "model"

    if not self_report:
        return resolved

    # --- Tone override ---
    tone_interval = model_result.get("tone_confidence_interval_90")
    tone_uncertain = tone_interval and (tone_interval[1] - tone_interval[0]) > TONE_INTERVAL_WIDTH_THRESHOLD

    tone_category = self_report.get("tone_category")
    if tone_category and tone_category in TONE_CATEGORY_TO_RANGE:
        low, high = TONE_CATEGORY_TO_RANGE[tone_category]
        midpoint = (low + high) / 2
        if tone_uncertain:
            # Model was unsure -> trust the user's self-report instead
            resolved["skin_tone_fitzpatrick_estimate"] = midpoint
            resolved["tone_confidence_interval_90"] = [low, high]
            resolved["tone_source"] = "user_self_report (model was low-confidence)"
        else:
            # Model was confident -> keep model value, but note the user's input for reference
            resolved["user_reported_tone_category"] = tone_category

    # --- Skin type override ---
    type_confidence = model_result.get("skin_type_confidence", 0)
    self_type = self_report.get("skin_type")
    if self_type:
        if type_confidence < TYPE_CONFIDENCE_THRESHOLD:
            resolved["skin_type"] = self_type
            resolved["skin_type_confidence"] = 1.0  # user-provided, treated as ground truth
            resolved["type_source"] = "user_self_report (model was low-confidence)"
        else:
            resolved["user_reported_skin_type"] = self_type

    return resolved