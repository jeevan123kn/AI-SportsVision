import os
import uuid
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import Session as SessionRecord, Player, get_db
from services.feature_extractor import extract_features
from services.performance_analyzer import PerformanceAnalyzer
from services.weakness_detector import WeaknessDetector
from services.mistake_detector import MistakeDetector
from services.prediction_engine import PredictionEngine
from services.coaching_engine import CoachingEngine
from services.video_processor import VideoProcessor, validate_video
from services.pose_estimator import PoseEstimator

router = APIRouter(prefix="/api", tags=["analysis"])


class AnalysisRequest(BaseModel):
    player_id: str = Field(...)
    sport: str = "Cricket"
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
    pose_metrics = []
    for frame in frames:
        results, landmarks = estimator.estimate_pose(frame)
        if landmarks:
            metrics = extract_features(landmarks)
            if metrics.get("status") == "Pose data available":
                pose_metrics.append(metrics["metrics"])

    if not pose_metrics:
        raise HTTPException(status_code=422, detail="Pose estimation failed. No valid landmarks detected.")

    avg_metrics = {}
    for key in set().union(*(d.keys() for d in pose_metrics)):
        values = [d.get(key) for d in pose_metrics if d.get(key) is not None]
        if values:
            avg_metrics[key] = sum(values) / len(values)

    avg_metrics.setdefault("balance_score", 0.7)
    avg_metrics.setdefault("movement_score", 0.72)
    avg_metrics.setdefault("movement_consistency", 0.68)
    avg_metrics.setdefault("stability_score", 0.74)

    analyzer = PerformanceAnalyzer()
    analysis = analyzer.analyze(avg_metrics)

    weakness_detector = WeaknessDetector()
    weaknesses = weakness_detector.detect(avg_metrics)

    prior_sessions = []
    history = db.query(SessionRecord).filter(SessionRecord.player_id == payload.player_id).all()
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
    recommendations = coaching_engine.generate_recommendations(weaknesses, repeated_mistakes, prediction)

    session_id = str(uuid.uuid4())
    record = SessionRecord(
        id=session_id,
        player_id=payload.player_id,
        sport=payload.sport,
        activity=payload.activity,
        video_reference=payload.video_path,
        overall_score=float(analysis["overall_score"]),
        technique_score=float(analysis["component_scores"].get("technique", 0.0)),
        balance_score=float(analysis["component_scores"].get("balance", 0.0)),
        movement_score=float(analysis["component_scores"].get("movement", 0.0)),
        consistency_score=float(analysis["component_scores"].get("consistency", 0.0)),
        stability_score=float(analysis["component_scores"].get("stability", 0.0)),
        weaknesses=weaknesses,
        repeated_mistakes=repeated_mistakes,
        recommendations=recommendations,
        prediction_data=prediction,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "session_id": session_id,
        "player": player.name,
        "sport": payload.sport,
        "activity": payload.activity,
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
        "weaknesses": weaknesses,
        "repeated_mistakes": repeated_mistakes,
        "prediction": prediction,
        "recommendations": recommendations,
    }
