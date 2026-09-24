import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import Player, Session as SessionRecord, get_db

router = APIRouter(prefix="/api", tags=["history"])


class LiveSessionPayload(BaseModel):
    player_id: str = Field(...)
    sport: str = "Cricket"
    activity: str = "Batting"
    duration_seconds: int = 0
    overall_score: float = 0.0
    technique_score: float = 0.0
    balance_score: float = 0.0
    movement_score: float = 0.0
    consistency_score: float = 0.0
    stability_score: float = 0.0
    weaknesses: list[dict] | None = None
    recommendations: list[dict] | None = None
    ai_insight: str | None = None


@router.post("/live-session")
def create_live_session(payload: LiveSessionPayload, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == payload.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    session_id = str(uuid.uuid4())
    session = SessionRecord(
        id=session_id,
        player_id=payload.player_id,
        sport=payload.sport,
        activity=payload.activity,
        overall_score=float(payload.overall_score or 0.0),
        technique_score=float(payload.technique_score or 0.0),
        balance_score=float(payload.balance_score or 0.0),
        movement_score=float(payload.movement_score or 0.0),
        consistency_score=float(payload.consistency_score or 0.0),
        stability_score=float(payload.stability_score or 0.0),
        weaknesses=payload.weaknesses or [],
        repeated_mistakes=[],
        recommendations=payload.recommendations or [{"title": "Live coaching", "description": payload.ai_insight or "Continue with the current movement pattern and focus on balance control.", "reason": "Detected from the live session."}],
        prediction_data={"source": "LIVE CAMERA", "duration_seconds": payload.duration_seconds, "ai_insight": payload.ai_insight or "Session complete"},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "player_id": session.player_id,
        "sport": session.sport,
        "activity": session.activity,
        "overall_score": session.overall_score,
        "technique_score": session.technique_score,
        "balance_score": session.balance_score,
        "movement_score": session.movement_score,
        "consistency_score": session.consistency_score,
        "stability_score": session.stability_score,
    }


@router.get("/history/{player_id}")
def get_history(player_id: str, db: Session = Depends(get_db)):
    sessions = db.query(SessionRecord).filter(SessionRecord.player_id == player_id).order_by(SessionRecord.date.desc()).all()
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found for player")

    return [{
        "id": session.id,
        "date": session.date.isoformat(),
        "sport": session.sport,
        "activity": session.activity,
        "overall_score": session.overall_score,
        "technique_score": session.technique_score,
        "balance_score": session.balance_score,
        "movement_score": session.movement_score,
        "consistency_score": session.consistency_score,
        "stability_score": session.stability_score,
        "weaknesses": session.weaknesses,
        "repeated_mistakes": session.repeated_mistakes,
        "recommendations": session.recommendations,
        "prediction_data": session.prediction_data,
    } for session in sessions]
