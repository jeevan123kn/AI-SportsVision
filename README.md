# AI SportsVision

AI SportsVision is a modular sports performance analysis application focused on cricket batting analysis first, with extensible architecture for other sports.

## Tech stack
- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy + SQLite
- Computer vision: OpenCV + MediaPipe
- Analysis: Python feature extraction and scoring

## Getting started

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Current MVP capabilities
- Player creation
- Video upload validation
- Video frame extraction
- MediaPipe pose estimation
- Feature extraction for batting posture metrics
- Performance analysis scoring
- Weakness detection
- Repeated mistake detection using history
- Prediction trend analysis
- Personalized coaching recommendations
- Session storage and comparison
