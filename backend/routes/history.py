import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import Player, Session as SessionRecord, get_db

router = APIRouter(prefix="/api", tags=["history"])


class LiveSessionPayload(BaseModel):
    player_id: str = Field(...)
    sport: str = "Cricket"
    role: str | None = None
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
    pose_frames: list[list[dict]] = Field(default_factory=list, max_length=180)
    sampled_frames: int | None = None


@router.post("/live-session")
def create_live_session(payload: LiveSessionPayload, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == payload.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    analysis = None
    prediction = None
    repeated_mistakes = []
    selected_sport = payload.sport or player.sport
    selected_role = payload.role or player.role
    selected_activity = payload.activity or player.preferred_activity
    weaknesses = payload.weaknesses or []
    recommendations = payload.recommendations or []
    overall_score = float(payload.overall_score or 0.0)
    component_scores = {
        "technique": float(payload.technique_score or 0.0),
        "balance": float(payload.balance_score or 0.0),
        "movement": float(payload.movement_score or 0.0),
        "consistency": float(payload.consistency_score or 0.0),
        "stability": float(payload.stability_score or 0.0),
    }
    if payload.pose_frames or payload.sampled_frames is not None:
        from services.sport_analysis_engine import SportAnalysisEngine

        analysis = SportAnalysisEngine().analyze(
            selected_sport,
            selected_role,
            selected_activity,
            payload.pose_frames,
            sampled_frames=payload.sampled_frames or len(payload.pose_frames),
            duration_seconds=payload.duration_seconds,
        )
        if analysis["overall_score"] is None:
            raise HTTPException(status_code=422, detail=analysis["status"])
        overall_score = float(analysis["overall_score"])
        component_scores = {key: float(analysis.get(f"{key}_score") or 0.0) for key in component_scores}
        weaknesses = analysis["weaknesses"]
        recommendations = [
            {"title": item["feature"], "description": item["suggested_improvement"], "reason": item["evidence"]}
            for item in weaknesses
        ]
        previous_sessions = db.query(SessionRecord).filter(
            SessionRecord.player_id == payload.player_id,
            SessionRecord.sport == selected_sport,
            SessionRecord.activity == selected_activity,
        ).all()
        from services.coaching_engine import CoachingEngine
        from services.mistake_detector import MistakeDetector
        from services.prediction_engine import PredictionEngine

        prior_patterns = [{"weaknesses": item.weaknesses or [], "overall_score": item.overall_score} for item in previous_sessions]
        repeated_mistakes = MistakeDetector().detect(prior_patterns, weaknesses)
        prior_scores = [item.overall_score for item in previous_sessions if item.overall_score]
        prediction = PredictionEngine().predict(prior_scores, overall_score)
        recommendations = CoachingEngine().generate_recommendations(
            weaknesses,
            repeated_mistakes,
            prediction,
            sport=selected_sport,
            role=selected_role,
            activity=selected_activity,
        )
        if not recommendations:
            recommendations = [{"title": "Next session", "description": f"Capture another full-body {selected_activity or selected_sport} sequence to check whether these measured movement patterns are repeatable.", "reason": "No pose-supported corrective issue was detected in this session."}]

    session_id = str(uuid.uuid4())
    session = SessionRecord(
        id=session_id,
        player_id=payload.player_id,
        sport=selected_sport,
        activity=selected_activity,
        overall_score=overall_score,
        technique_score=component_scores["technique"],
        balance_score=component_scores["balance"],
        movement_score=component_scores["movement"],
        consistency_score=component_scores["consistency"],
        stability_score=component_scores["stability"],
        weaknesses=weaknesses,
        repeated_mistakes=repeated_mistakes,
        recommendations=recommendations or [{"title": "Live coaching", "description": payload.ai_insight or "Capture another session for further analysis.", "reason": "No additional pose-based recommendation was supplied."}],
        prediction_data={"source": "LIVE CAMERA", "duration_seconds": payload.duration_seconds, "ai_insight": analysis["ai_analysis"] if analysis else payload.ai_insight, "role": selected_role, "sport_analysis": analysis, "prediction": prediction},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "player_id": session.player_id,
        "sport": session.sport,
        "activity": session.activity,
        "role": payload.role or player.role,
        "overall_score": session.overall_score,
        "technique_score": _session_component_score(session, "technique"),
        "balance_score": _session_component_score(session, "balance"),
        "movement_score": _session_component_score(session, "movement"),
        "consistency_score": _session_component_score(session, "consistency"),
        "stability_score": _session_component_score(session, "stability"),
        "analysis": analysis,
        **(analysis or {}),
        "weaknesses": weaknesses,
        "recommendations": session.recommendations,
        "repeated_mistakes": repeated_mistakes,
        "prediction": prediction,
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
        "role": (session.prediction_data or {}).get("role"),
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
        "role_adherence_score": ((session.prediction_data or {}).get("sport_analysis") or {}).get("role_adherence", {}).get("score"),
        "activity_performance_score": ((session.prediction_data or {}).get("sport_analysis") or {}).get("activity_performance", {}).get("score"),
        "performance_analysis": (session.prediction_data or {}).get("sport_analysis"),
    } for session in sessions]


def _session_component_score(session, name):
    analysis = (session.prediction_data or {}).get("sport_analysis")
    if analysis is not None:
        return (analysis.get("component_scores") or {}).get(name)
    return getattr(session, f"{name}_score")
