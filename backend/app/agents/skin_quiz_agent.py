"""
Skin Type Questionnaire Agent: a structured self-assessment, the same
approach dermatologists and estheticians actually use for a first-pass
skin type read -- more diagnostic than a single dropdown pick, and doesn't
depend on photo quality/lighting the way the vision model does.
"""

QUESTIONS = [
    {
        "id": "midday_shine",
        "question": "By midday, how does your skin usually look/feel?",
        "options": {
            "shiny_all_over": {"oily": 2},
            "shiny_tzone_only": {"oily": 1, "normal": 1},
            "same_as_morning": {"normal": 2},
            "tight_or_flaky": {"dry": 2},
        },
    },
    {
        "id": "pores",
        "question": "How visible are your pores, generally?",
        "options": {
            "very_visible": {"oily": 2},
            "somewhat_visible_tzone": {"oily": 1, "normal": 1},
            "barely_visible": {"normal": 1, "dry": 1},
            "not_visible": {"dry": 2},
        },
    },
    {
        "id": "after_cleansing",
        "question": "Right after washing your face, how does it feel?",
        "options": {
            "tight_uncomfortable": {"dry": 2},
            "slightly_tight_briefly": {"normal": 1, "dry": 1},
            "comfortable": {"normal": 2},
            "still_a_bit_oily": {"oily": 2},
        },
    },
    {
        "id": "breakouts",
        "question": "How often do you experience breakouts/blackheads?",
        "options": {
            "frequently": {"oily": 2},
            "occasionally": {"normal": 1, "oily": 1},
            "rarely": {"normal": 1, "dry": 1},
            "almost_never_but_flaky": {"dry": 2},
        },
    },
    {
        "id": "flaking",
        "question": "Do you notice flaky or rough patches?",
        "options": {
            "frequently": {"dry": 2},
            "occasionally_in_dry_seasons": {"dry": 1, "normal": 1},
            "rarely": {"normal": 1, "oily": 1},
            "never": {"oily": 2},
        },
    },
]


def get_questionnaire() -> list[dict]:
    """Returns just the questions/options for the frontend to render."""
    return [
        {"id": q["id"], "question": q["question"], "options": list(q["options"].keys())}
        for q in QUESTIONS
    ]


def score_questionnaire(answers: dict) -> dict:
    """
    answers: {question_id: selected_option_key}
    Returns the resulting skin type plus a transparent score breakdown.
    """
    scores = {"oily": 0, "dry": 0, "normal": 0}
    unanswered = []

    for q in QUESTIONS:
        selected = answers.get(q["id"])
        if selected and selected in q["options"]:
            for skin_type, points in q["options"][selected].items():
                scores[skin_type] += points
        else:
            unanswered.append(q["id"])

    result_type = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    confidence = round(scores[result_type] / total, 2)

    return {
        "skin_type": result_type,
        "confidence": confidence,
        "score_breakdown": scores,
        "unanswered_questions": unanswered,
        "method": "weighted self-assessment questionnaire",
    }