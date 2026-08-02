"""
Coordinator Agent: the "agents talking to each other" layer.

Takes the Vision Agent's output (skin profile) and the Ingredient Agent's
output (product risk flags), cross-references them, and produces one
personalized, confidence-aware report. This is the genuine multi-agent
reasoning piece -- not just running two models and concatenating results.
"""

TYPE_CONFIDENCE_THRESHOLD = 0.5   # below this, we treat skin-type as uncertain
TONE_INTERVAL_WIDTH_THRESHOLD = 2.5  # wider than this on a 1-6 scale = low trust


def cross_reference(vision_result: dict, ingredient_result: dict) -> dict:
    """
    The core coordination logic: looks for agreement, disagreement, and
    compounding risk between the two agents' outputs.
    """
    notes = []
    elevated_flags = []
    uncertainty_flags = []

    skin_type = vision_result.get("skin_type")
    type_confidence = vision_result.get("skin_type_confidence", 0)
    acne_probability = vision_result.get("acne_probability", 0)

    tone_interval = vision_result.get("tone_confidence_interval_90")
    tone_uncertain = False
    if tone_interval:
        width = tone_interval[1] - tone_interval[0]
        if width > TONE_INTERVAL_WIDTH_THRESHOLD:
            tone_uncertain = True
            uncertainty_flags.append(
                "Skin tone estimate has a wide confidence interval -- treat as rough guidance only."
            )

    if type_confidence < TYPE_CONFIDENCE_THRESHOLD:
        uncertainty_flags.append(
            f"Skin type prediction ('{skin_type}') has low confidence ({round(type_confidence * 100)}%) "
            "-- personalized flags below are based on this uncertain estimate."
        )

    # Cross-agent reasoning: does the product's ingredient risk COMPOUND with the detected skin profile?
    matched = ingredient_result.get("ingredients", [])
    for item in matched:
        if not item.get("matched"):
            continue
        rating = item.get("comedogenic_rating", 0)
        tier = item.get("estimated_tier")
        name = item.get("matched_ingredient")

        if skin_type == "oily" and rating >= 3 and tier in ("primary", "moderate"):
            elevated_flags.append(
                f"'{name}' is a notable comedogenic ingredient at meaningful concentration, "
                f"and your detected skin type is oily -- this combination is worth extra caution."
            )

        if acne_probability >= 0.5 and rating >= 3 and tier in ("primary", "moderate"):
            elevated_flags.append(
                f"'{name}' may not be ideal given the acne indicators detected in your photo."
            )

        if item.get("is_common_allergen"):
            notes.append(f"'{name}' is a common allergen/irritant -- patch-test before full use.")

    return {
        "elevated_flags": elevated_flags,
        "general_notes": notes,
        "uncertainty_flags": uncertainty_flags,
        "requires_debate": tone_uncertain or type_confidence < TYPE_CONFIDENCE_THRESHOLD,
    }


def build_combined_report(vision_result: dict, ingredient_result: dict) -> dict:
    coordination = cross_reference(vision_result, ingredient_result)

    return {
        "skin_profile": vision_result,
        "product_analysis": ingredient_result,
        "coordinated_insights": coordination,
        "overall_disclaimer": (
            "This report combines automated skin analysis and ingredient analysis. "
            "It is not a medical diagnosis. Please verify with a licensed dermatologist "
            "before making treatment or product decisions."
        ),
    }