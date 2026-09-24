from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import Session as SessionRecord, get_db
from services.prediction_engine import PredictionEngine

router = APIRouter(prefix="/api", tags=["prediction"])


@router.get("/prediction/{player_id}")
def get_prediction(player_id: str, db: Session = Depends(get_db)):
    sessions = db.query(SessionRecord).filter(SessionRecord.player_id == player_id).order_by(SessionRecord.date.asc()).all()
    scores = [session.overall_score for session in sessions if session.overall_score]
    current = scores[-1] if scores else 0.0
    engine = PredictionEngine()
    prediction = engine.predict(scores, current)
    return {"player_id": player_id, "history": scores, "prediction": prediction}
