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
        component_name = metric.removesuffix("_score")
        a_value = _session_score(a, metric, component_name)
        b_value = _session_score(b, metric, component_name)
        if a_value is None or b_value is None:
            comparison[metric] = {"session_a": a_value, "session_b": b_value, "difference": None, "status": "Unavailable"}
            continue
        diff = b_value - a_value
        if diff > 2:
            status = "Improved"
        elif diff < -2:
            status = "Needs Attention"
        else:
            status = "Stable"
        comparison[metric] = {"session_a": a_value, "session_b": b_value, "difference": diff, "status": status}

    for metric, key in (("role_adherence", "role_adherence"), ("activity_performance", "activity_performance")):
        first_analysis = ((a.prediction_data or {}).get("sport_analysis") or {})
        second_analysis = ((b.prediction_data or {}).get("sport_analysis") or {})
        first_value = (first_analysis.get(key) or {}).get("score")
        second_value = (second_analysis.get(key) or {}).get("score")
        if first_value is not None and second_value is not None:
            diff = second_value - first_value
            status = "Improved" if diff > 2 else "Needs Attention" if diff < -2 else "Stable"
            comparison[metric] = {"session_a": first_value, "session_b": second_value, "difference": diff, "status": status}

    return {"session_a": a.id, "session_b": b.id, "comparison": comparison}


def _session_score(session, metric, component_name):
    analysis = (session.prediction_data or {}).get("sport_analysis")
    if analysis is None:
        return getattr(session, metric)
    if metric == "overall_score":
        return analysis.get("overall_score")
    return (analysis.get("component_scores") or {}).get(component_name)
