"""
Seeds a starter symptom-keyword-to-possible-cause knowledge base.

HONESTY NOTE (mention in your README): this is an educational reference
for common, well-known dermatological patterns -- not a diagnostic system.
Urgency flags are intentionally conservative (err toward recommending a
doctor visit) since this is health-adjacent.

Run with:  python -m app.db.seed_symptom_knowledge
"""
from app.db.database import SessionLocal, Base, engine
from app.models.models import SymptomKnowledge

Base.metadata.create_all(bind=engine)

KNOWLEDGE = [
    # keyword, possible_cause, category, urgency, note
    ("itchy", "Possible allergic or irritant contact reaction", "allergy", "routine",
     "Common with new products, detergents, or fabric contact."),
    ("burning", "Possible irritant reaction or over-exfoliation", "irritation", "prompt",
     "Can indicate skin barrier damage, especially after actives like retinol/acids."),
    ("red patches", "Possible eczema, contact dermatitis, or heat rash", "irritation", "routine", None),
    ("flaky", "Possible dryness, eczema, or barrier disruption", "irritation", "routine", None),
    ("bumps", "Possible folliculitis, allergic reaction, or heat rash", "irritation", "routine", None),
    ("pus", "Possible infection", "infection-signal", "urgent",
     "Pus, warmth, and spreading redness together warrant prompt medical evaluation."),
    ("swelling", "Possible allergic reaction or infection", "allergy", "urgent",
     "Rapid or spreading swelling, especially near eyes/mouth/throat, needs urgent care."),
    ("bleeding", "Possible skin breakdown or injury requiring evaluation", "infection-signal", "urgent", None),
    ("spreading rapidly", "Possible infection or acute allergic reaction", "infection-signal", "urgent", None),
    ("dark patch", "Possible hyperpigmentation, sun damage, or (rarely) something requiring evaluation", "sun-related", "prompt",
     "New or changing dark patches should be evaluated by a dermatologist, especially if changing shape/size."),
    ("worse in sun", "Possible photosensitivity or sun-triggered reaction", "sun-related", "routine", None),
    ("after new product", "Possible product-related irritant or allergic reaction", "allergy", "routine",
     "Consider discontinuing the suspected product and monitoring."),
    ("painful", "Possible infection, cyst, or nerve-related irritation", "infection-signal", "prompt", None),
    ("fever", "Possible systemic infection alongside skin symptoms", "infection-signal", "urgent", None),
    ("dry cracking", "Possible severe dryness or eczema flare", "irritation", "routine", None),
    ("odor", "Possible infection", "infection-signal", "prompt", None),
]


def seed():
    db = SessionLocal()
    added = 0
    for keyword, cause, category, urgency, note in KNOWLEDGE:
        existing = db.query(SymptomKnowledge).filter(SymptomKnowledge.keyword == keyword).first()
        if existing:
            continue
        db.add(SymptomKnowledge(
            keyword=keyword, possible_cause=cause, category=category, urgency=urgency, note=note,
        ))
        added += 1
    db.commit()
    total = db.query(SymptomKnowledge).count()
    db.close()
    print(f"Added {added} new entries. Total in symptom knowledge base: {total}")


if __name__ == "__main__":
    seed()