# SkinIQ 

A multi-agent AI system for skin health guidance — built to be genuinely useful, not just impressive-sounding. Upload a photo, get an honest confidence-scored analysis. Scan a product label, get real ingredient risk data. Describe a symptom, get guidance grounded in weather, product history, and community context — no photo required, ever, for private concerns.

This isn't a single model pretending to do everything. It's six specialized agents that reason about your skin together, cross-check each other, and are honest about what they don't know.
LIVE DEMO : https://www.linkedin.com/posts/aditi-raj-330459295_hi-im-going-to-show-you-a-project-i-built-ugcPost-7491060975115108352-b8i8/?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEdvk5QBYfJ9UV8Vn-FCLUDidVIViS9HHKY


---
 Why this exists

Most AI skincare tools give you one confident-sounding answer. That's the wrong design for anything health-adjacent. SkinIQ is built around a different idea: **show your uncertainty, on purpose.** Every prediction carries a real, statistically calibrated confidence range. When the model isn't sure, it says so — and lets you correct it instead of quietly guessing.

---

 The agents

| Agent | What it does | Key technique |
|---|---|---|
| Vision Agent** | Estimates skin tone, type, acne likelihood, and dark-circle likelihood from a face photo | Multi-task DINOv2 vision transformer + conformal prediction for calibrated confidence intervals |
| OCR + Ingredient Agent | Reads a product's ingredient label and flags risks | EasyOCR (deep learning OCR) + fuzzy substring matching against a 28,000-name cosmetic ingredient database (EU CosIng) |
| Coordinator Agent | Cross-references the Vision and Ingredient agents' outputs, elevates compounding risks, flags when agents disagree | Rule-based cross-agent reasoning with confidence gating |
| Profile Resolver | Lets users self-report skin tone/type when the model's own confidence is too low to trust | Confidence-threshold-based override logic |
| Recommendation Agent** | Matches products to a user's skin profile with a plain-language reason for every suggestion | Content-based filtering (not a black-box score) |
| Symptom Agent | Analyzes a described symptom against weather, UV, recent product history, and community trend data — text only, so private-area concerns never require a photo | Fuzzy keyword-to-cause matching + Open-Meteo weather API + haversine-based local trend aggregation |

---

What makes this different from a typical portfolio ML project

- Conformal prediction, not fake confidence.** Every skin-tone estimate ships with a statistically valid interval, calibrated on held-out data — not an invented percentage.
- Partial-label multi-task learning.** The vision model is trained across three separate, non-overlapping datasets (Fitzpatrick17k, a Kaggle skin-type set, and a small acne/dark-circle set), each batch only backpropagating through the heads it has ground truth for.
- Honest data-scarcity handling.** The acne/dark-circle heads are trained on a genuinely small dataset — the system says so, in the response, rather than pretending otherwise.
- A real ingredient reference, not a toy list.** 28,000+ INCI names sourced from the EU's official cosmetic ingredient database, cross-referenced against a curated risk table for comedogenicity and allergen flags.
- Privacy-by-design, not privacy-by-policy.** The symptom-reporting endpoint has no image field in its schema at all — private-area concerns can't accidentally require a photo, because the code doesn't allow it.
- Gated medical-adjacent content.** OTC suggestions are never returned unless the user explicitly acknowledges they'll confirm with a dermatologist first — enforced server-side, not just a UI nag.
- Full audit trail.** Every agent decision is logged to SQL with its confidence and whether it triggered a "debate" — nothing is a black box.

---

 Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Frontend   │─────▶│   FastAPI Backend │─────▶│  SQLite / Postgres│
│ (HTML/CSS/JS)│      │                  │      │  (7+ tables)     │
└─────────────┘      │  ┌────────────┐  │      └─────────────────┘
                      │  │ Vision     │  │
                      │  │ OCR+Ingred.│  │      ┌─────────────────┐
                      │  │ Coordinator│  │─────▶│ 28k ingredient   │
                      │  │ Recommend  │  │      │ gazetteer (CosIng)│
                      │  │ Symptom    │  │      └─────────────────┘
                      │  │ Advisory   │  │
                      │  └────────────┘  │      ┌─────────────────┐
                      └──────────────────┘─────▶│ Open-Meteo API   │
                                                  │ (weather/UV)     │
                                                  └─────────────────┘
```

---

## Tech stack

**Backend:** FastAPI, SQLAlchemy, SQLite (Postgres-ready)
**ML/CV:** PyTorch, timm (DINOv2 ViT backbone), conformal prediction, EasyOCR
**NLP:** RapidFuzz (fuzzy entity matching), keyword-based symptom classification
**Frontend:** Vanilla HTML/CSS/JS — no build step, no framework overhead
**Training:** Google Colab (T4 GPU), Fitzpatrick17k + Kaggle skin-type + acne/dark-circle datasets

---

## Honest limitations

Worth stating plainly, because pretending otherwise would undercut the whole design philosophy of this project:

- The acne and dark-circle model heads are trained on a very small dataset (~30 images) — treated as indicative, not reliable, and the API says so in every response.
- The curated ingredient risk database (~80 ingredients) is a starter set, not dermatologist-verified — flagged in every relevant response.
- Community trend data is only meaningful once enough reports accumulate; with sparse demo data it honestly reports "not enough data yet" rather than fabricating a signal.
- This is a portfolio project demonstrating system design, not a validated medical product.

---

## Running it locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m app.db.seed_ingredients
python -m app.db.seed_gazetteer
python -m app.db.seed_products
python -m app.db.seed_symptom_knowledge
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
python3 -m http.server 8080
```

Then visit `http://localhost:8080`.

---

## What's next

- Postgres migration for real concurrent usage
- Expanding the curated ingredient risk database with dermatologist-verified data
- Collaborative-filtering upgrade to the recommendation engine once real usage data exists
- Model retraining on the full Fitzpatrick17k set (currently a 3,000-image subset) for tighter confidence intervals

---

*SkinIQ is a demonstration of multi-agent ML system design. It is not a substitute for professional medical or dermatological advice.*
