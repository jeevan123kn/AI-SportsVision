from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import Session as SessionRecord, get_db

router = APIRouter(prefix="/api", tags=["comparison"])


@router.get("/comparison")
def compare_sessions(session_a: str, session_b: str, db: Session = Depends(get_db)):
    a = db.query(SessionRecord).filter(SessionRecord.id == session_a).first()
    b = db.query(SessionRecord).filter(SessionRecord.id == session_b).first()
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both sessions were not found")

    metrics = ["overall_score", "technique_score", "balance_score", "movement_score", "consistency_score", "stability_score"]
    comparison = {}
    for metric in metrics:
        a_value = getattr(a, metric)
        b_value = getattr(b, metric)
        diff = b_value - a_value
        if diff > 2:
            status = "Improved"
        elif diff < -2:
            status = "Declined"
        else:
            status = "No significant change"
        comparison[metric] = {"session_a": a_value, "session_b": b_value, "difference": diff, "status": status}

    return {"session_a": a.id, "session_b": b.id, "comparison": comparison}
