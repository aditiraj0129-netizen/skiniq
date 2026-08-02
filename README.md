# SkinIQ — Trust-First Multi-Agent Skin Health Advisor

A multi-agent system that analyzes skin photos, reasons about product ingredients,
and gives personalized skincare/makeup recommendations — always as suggestions,
never as medical diagnoses, always with confidence scores attached.

## Project status: Phase 1 (backend skeleton + SQL schema) — DONE
Next phase: multi-task vision model.

---

## How to set this up in VS Code, exactly, step by step

### 1. Open the project
- Open VS Code
- File -> Open Folder -> select the `skiniq` folder

### 2. Install the Python extension (if you haven't)
- Go to the Extensions tab (left sidebar, looks like 4 squares)
- Search "Python" (by Microsoft), install it

### 3. Open a terminal inside VS Code
- Menu: Terminal -> New Terminal
- It should open at the `skiniq/` root. Move into the backend folder:
```bash
cd backend
```

### 4. Create a virtual environment (isolates this project's Python packages)
```bash
python -m venv venv
```
Activate it:
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

You'll know it worked because your terminal prompt will show `(venv)` at the start.

**Important VS Code step**: press `Ctrl+Shift+P` (Cmd+Shift+P on Mac) -> type
"Python: Select Interpreter" -> choose the one inside `backend/venv`. This makes
VS Code's autocomplete/linting use the right environment.

### 5. Install dependencies
```bash
pip install -r requirements.txt
```
This will take a few minutes (torch is large). If you hit errors on `torch`, tell me
your OS and I'll give you the exact right install command for your machine.

### 6. Set up your environment file
```bash
cp .env.example .env
```
(On Windows, if `cp` doesn't work: `copy .env.example .env`)
You don't need to change anything yet — SQLite works out of the box for local dev.

### 7. Run the server
```bash
uvicorn app.main:app --reload
```
You should see something like `Uvicorn running on http://127.0.0.1:8000`

### 8. Verify it works
Open your browser to:
- http://127.0.0.1:8000/health → should show `{"status":"ok",...}`
- http://127.0.0.1:8000/docs → interactive API documentation (this is auto-generated
  by FastAPI from our code — very useful for testing endpoints as we build them)

If you see the docs page, **Phase 1 is complete and working.**

---

## Project structure explained

```
skiniq/
├── backend/
│   ├── app/
│   │   ├── main.py          <- FastAPI app entrypoint
│   │   ├── db/database.py   <- DB connection setup
│   │   ├── models/
│   │   │   ├── models.py    <- SQL tables (SQLAlchemy)
│   │   │   └── schemas.py   <- API request/response shapes (Pydantic)
│   │   ├── api/              <- (next) route files, one per feature
│   │   ├── agents/           <- (next) each agent's logic lives here
│   │   └── ml/                <- (next) trained models, inference code
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 <- (later) React app
└── docs/                     <- architecture notes, diagrams
```

## Design principles (keep these in mind as we build every feature)
1. **Never diagnose.** Every output is phrased as a possibility/recommendation with a disclaimer.
2. **Show confidence, always.** No bare predictions — every ML output carries a confidence value or interval.
3. **No photos for sensitive-area concerns.** Enforced at the database schema level, not just the UI.
4. **Full audit trail.** Every agent decision is logged (see `AgentOutputLog` table) so nothing is a black box.

## What's next
Phase 2: the multi-task vision model (skin tone, type, texture, concerns) with
conformal prediction for trustworthy confidence intervals. We'll pick a dataset,
set up training, and wire the trained model into a `/api/skin/analyze` endpoint.
