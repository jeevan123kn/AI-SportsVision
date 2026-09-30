import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import Session as SessionRecord, Player, get_db
from services.sport_analysis_engine import SportAnalysisEngine
from services.mistake_detector import MistakeDetector
from services.prediction_engine import PredictionEngine
from services.coaching_engine import CoachingEngine
from services.video_processor import VideoProcessor, validate_video
from services.pose_estimator import PoseEstimator

router = APIRouter(prefix="/api", tags=["analysis"])


class AnalysisRequest(BaseModel):
    player_id: str = Field(...)
    sport: str = "Cricket"
    role: str | None = None
    activity: str = "Batting"
    video_path: str = Field(...)


@router.post("/analyze")
def analyze_video(payload: AnalysisRequest, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == payload.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if not validate_video(payload.video_path):
        raise HTTPException(status_code=400, detail="Invalid video file")

    processor = VideoProcessor(payload.video_path)
    frames = processor.extract_frames(sample_every=6, limit=40)
    if not frames:
        raise HTTPException(status_code=400, detail="Unable to extract frames from video")

    estimator = PoseEstimator()
    pose_frames = []
    try:
        for frame in frames:
            _, landmarks = estimator.estimate_pose(frame)
            if landmarks:
                pose_frames.append(landmarks)
    finally:
        estimator.pose.close()

    selected_role = payload.role or player.role
    selected_sport = payload.sport or player.sport
    selected_activity = payload.activity or player.preferred_activity
    duration_seconds = processor.total_frames / processor.fps if processor.fps > 0 else None
    analysis = SportAnalysisEngine().analyze(
        selected_sport,
        selected_role,
        selected_activity,
        pose_frames,
        sampled_frames=len(frames),
        duration_seconds=duration_seconds,
    )
    if analysis["overall_score"] is None:
        raise HTTPException(status_code=422, detail=analysis["status"])

    weaknesses = analysis["weaknesses"]

    prior_sessions = []
    history = db.query(SessionRecord).filter(
        SessionRecord.player_id == payload.player_id,
        SessionRecord.sport == selected_sport,
        SessionRecord.activity == selected_activity,
    ).all()
    for session in history:
        prior_sessions.append({
            "weaknesses": session.weaknesses or [],
            "overall_score": session.overall_score,
        })

    mistake_detector = MistakeDetector()
    repeated_mistakes = mistake_detector.detect(prior_sessions, weaknesses)

    history_scores = [session.overall_score for session in history if session.overall_score]
    prediction_engine = PredictionEngine()
    prediction = prediction_engine.predict(history_scores, analysis["overall_score"])

    coaching_engine = CoachingEngine()
    recommendations = coaching_engine.generate_recommendations(
        weaknesses,
        repeated_mistakes,
        prediction,
        sport=selected_sport,
        role=selected_role,
        activity=selected_activity,
    )

    session_id = str(uuid.uuid4())
    record = SessionRecord(
        id=session_id,
        player_id=payload.player_id,
        sport=selected_sport,
        activity=selected_activity,
        video_reference=payload.video_path,
        overall_score=float(analysis["overall_score"]),
        technique_score=float(analysis.get("technique_score") or 0.0),
        balance_score=float(analysis.get("balance_score") or 0.0),
        movement_score=float(analysis.get("movement_score") or 0.0),
        consistency_score=float(analysis.get("consistency_score") or 0.0),
        stability_score=float(analysis.get("stability_score") or 0.0),
        weaknesses=weaknesses,
        repeated_mistakes=repeated_mistakes,
        recommendations=recommendations,
        prediction_data={**prediction, "role": selected_role, "sport_analysis": analysis, "source": "VIDEO"},
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "session_id": session_id,
        "player": player.name,
        "sport": selected_sport,
        "role": selected_role,
        "activity": selected_activity,
        "processing_pipeline": [
            "Uploading",
            "Processing",
            "Player Detection",
            "Pose Analysis",
            "Feature Extraction",
            "Performance Analysis",
            "Prediction",
            "Coaching",
        ],
        "analysis": analysis,
        **analysis,
        "weaknesses": weaknesses,
        "repeated_mistakes": repeated_mistakes,
        "prediction": prediction,
        "recommendations": recommendations,
    }
