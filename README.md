# FaceInsight AI

**Premium AI-powered cosmetic facial analysis. Startup-ready.**

Upload a portrait → Get a direct, structured cosmetic report with prioritized recommendations across skincare, grooming, hairstyle, non-invasive options, and specialist consultations.

---

## Architecture
```
project/
├── frontend/          # Streamlit UI
│   └── app.py
├── backend/           # FastAPI REST API
│   ├── main.py
│   └── routers/
│       └── analysis.py
├── services/          # Business logic
│   ├── analysis_service.py      # Orchestrator
│   ├── face_detection_service.py # InsightFace + OpenCV fallback
│   ├── openai_service.py        # GPT-4o Vision
│   └── recommendation_engine.py # Priority ranking
├── models/
│   └── schemas.py     # Pydantic data models
├── prompts/
│   └── analysis_prompts.py  # System + user prompts
└── utils/
    ├── config.py
    ├── validators.py
    └── error_handlers.py
```

---

## Setup

### 1. Clone and install
```bash
git clone <repo>
cd project
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY
```

### 3. Download InsightFace model (first run)
InsightFace downloads `buffalo_l` automatically on first startup. Requires internet access.

### 4. Run backend
```bash
cd project
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run frontend
```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501`

---

## API

### `POST /api/v1/analyze`
Upload an image file (`multipart/form-data`, field name: `file`).

**Response:**
```json
{
  "success": true,
  "quality_check": { "passed": true, "score": 0.9, "issues": [], "face_detected": true, "face_count": 1 },
  "report": {
    "summary": "...",
    "skin_analysis": { ... },
    "face_structure": { ... },
    "eye_analysis": { ... },
    "skincare_recommendations": [...],
    "grooming_recommendations": [...],
    "hairstyle_recommendations": [...],
    "beard_recommendations": [...],
    "makeup_recommendations": [...],
    "non_invasive_options": [...],
    "injectables_to_discuss": [...],
    "procedural_surgical_consultation": [...],
    "what_not_to_do": [...],
    "disclaimer": "..."
  }
}
```

**Error (422 — quality check failed):**
```json
{
  "success": false,
  "error": {
    "message": "Image quality check failed.",
    "issues": ["Image appears blurry.", "No face detected."],
    "quality_score": 0.25
  }
}
```

**Docs:** `http://localhost:8000/docs`

---

## Recommendation Engine Logic

Recommendations are ranked using two keys:
1. **Intervention level** (ascending): `none → low → medium → high → specialist`
2. **Priority score** (ascending, 1 = most impactful)

This ensures the user always sees the highest-impact, lowest-effort actions first, and specialist options last.

---

## Image Requirements

| Requirement | Minimum |
|---|---|
| Resolution | 300 × 300 px |
| Sharpness | Laplacian variance > 80 |
| Brightness | 50–220 mean gray |
| Face count | Exactly 1 |
| Format | JPEG, PNG, WebP |
| File size | ≤ 10 MB |

---

## Tone & Ethics Policy

- **No ethnic/racial/national/religious inference** — the model is explicitly blocked from these inferences in the system prompt.
- **No medical diagnosis** — cosmetic observation only.
- **No exaggeration or false flattery** — premium, direct, honest.
- **Disclaimer** is embedded in every report.

---

## Deployment Notes

**Backend:** Deploy as a containerized FastAPI service (e.g., Railway, Fly.io, GCP Cloud Run). Set `OPENAI_API_KEY` as an environment secret.

**Frontend:** Deploy via Streamlit Cloud or as a Docker container. Update `API_URL` in `frontend/app.py` to point to your production backend URL.

**Docker (backend):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```