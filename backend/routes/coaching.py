from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import Session as SessionRecord, get_db

router = APIRouter(prefix="/api", tags=["coaching"])


@router.get("/coaching/{session_id}")
def get_coaching(session_id: str, db: Session = Depends(get_db)):
    session = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "weaknesses": session.weaknesses or [],
        "repeated_mistakes": session.repeated_mistakes or [],
        "recommendations": session.recommendations or [],
        "prediction": session.prediction_data or {},
    }
