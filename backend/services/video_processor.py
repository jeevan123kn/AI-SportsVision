import os
from pathlib import Path

import cv2
import numpy as np

from utils.config import settings


class VideoProcessor:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if self.cap.isOpened() else 0

    def extract_frames(self, sample_every: int = 6, limit: int = 60):
        if not self.cap.isOpened():
            raise ValueError("Unable to open video file")

        frames = []
        count = 0
        idx = 0

        while True:
            success, frame = self.cap.read()
            if not success:
                break
            if count % sample_every == 0:
                frames.append(frame)
                idx += 1
            count += 1
            if idx >= limit:
                break

        self.cap.release()
        return frames

    def extract_sample_metrics(self):
        frames = self.extract_frames()
        if not frames:
            return {
                "frame_count": 0,
                "duration_seconds": 0,
                "sampled_frames": 0,
                "status": "No frames extracted",
            }

        height, width = frames[0].shape[:2]
        return {
            "frame_count": len(frames),
            "duration_seconds": max(1, round(self.total_frames / max(1, 30), 2)),
            "sampled_frames": len(frames),
            "resolution": {"width": width, "height": height},
            "status": "Frames extracted successfully",
        }


def validate_video(video_path: str) -> bool:
    if not video_path or not os.path.exists(video_path):
        return False
    try:
        cap = cv2.VideoCapture(video_path)
        ok = cap.isOpened()
        cap.release()
        return ok
    except Exception:
        return False
