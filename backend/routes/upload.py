import os
import uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi"}
UPLOAD_ROOT = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: MP4, MOV, AVI")

    file_id = str(uuid.uuid4())
    destination = UPLOAD_ROOT / f"{file_id}{ext}"
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    destination.write_bytes(content)
    return {
        "file_id": file_id,
        "filename": file.filename,
        "path": str(destination),
        "status": "uploaded",
        "pipeline": [
            "Uploading",
            "Processing",
            "Player Detection",
            "Pose Analysis",
            "Feature Extraction",
            "Performance Analysis",
            "Prediction",
            "Coaching",
        ],
    }
