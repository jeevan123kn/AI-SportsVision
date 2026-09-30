import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import Base, Player, get_db
from routes import analysis as video_analysis
from routes.comparison import router as comparison_router
from routes.history import router as history_router


def pose_frame(offset=0.0):
    frame = [{"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.95} for _ in range(33)]
    for index, x, y in ((0, 0.5, 0.25), (11, 0.4, 0.4), (12, 0.6, 0.4), (23, 0.44, 0.65), (24, 0.56, 0.65), (25, 0.44, 0.8), (26, 0.56, 0.8), (27, 0.4, 0.95), (28, 0.6, 0.95)):
        frame[index].update(x=x + offset, y=y)
    return frame


class LiveAnalysisApiTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=engine)
        self.app = FastAPI()
        self.app.include_router(video_analysis.router)
        self.app.include_router(history_router)
        self.app.include_router(comparison_router)

        def override_get_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)
        with self.session_factory() as db:
            db.add(Player(id="player-1", name="Test Athlete", sport="Cricket", role="Batter", preferred_activity="Batting"))
            db.commit()

    def tearDown(self):
        self.client.close()

    def test_live_pose_analysis_returns_legacy_and_additive_fields(self):
        response = self.client.post("/api/live-session", json={
            "player_id": "player-1",
            "sport": "Cricket",
            "role": "Batter",
            "activity": "Batting",
            "duration_seconds": 8,
            "sampled_frames": 10,
            "pose_frames": [pose_frame(index * 0.002) for index in range(10)],
        })
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertIn("overall_score", result)
        self.assertIn("technique_score", result)
        self.assertIn("analysis", result)
        self.assertEqual(result["analysis"]["role_adherence"]["availability"], "estimated")
        self.assertEqual(result["analysis"]["data_quality"]["valid_frames"], 10)

        history = self.client.get("/api/history/player-1")
        self.assertEqual(history.status_code, 200)
        saved = history.json()[0]
        self.assertEqual(saved["role"], "Batter")
        self.assertIsNotNone(saved["performance_analysis"]["activity_performance"]["score"])

    def test_legacy_live_payload_still_returns_existing_score_fields(self):
        response = self.client.post("/api/live-session", json={
            "player_id": "player-1",
            "sport": "Cricket",
            "activity": "Batting",
            "overall_score": 63,
            "technique_score": 61,
            "balance_score": 62,
        })
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["overall_score"], 63)
        self.assertEqual(result["technique_score"], 61)
        self.assertIsNone(result["analysis"])

    def test_empty_new_pose_capture_is_rejected_instead_of_saving_zero_scores(self):
        response = self.client.post("/api/live-session", json={
            "player_id": "player-1",
            "sport": "Cricket",
            "role": "Batter",
            "activity": "Batting",
            "duration_seconds": 5,
            "pose_frames": [],
            "sampled_frames": 8,
        })
        self.assertEqual(response.status_code, 422)
        history = self.client.get("/api/history/player-1")
        self.assertEqual(history.status_code, 404)

    def test_single_frame_consistency_stays_unavailable_in_history_comparison(self):
        analyzed = self.client.post("/api/live-session", json={
            "player_id": "player-1",
            "sport": "Cricket",
            "role": "Batter",
            "activity": "Batting",
            "duration_seconds": 8,
            "sampled_frames": 10,
            "pose_frames": [pose_frame()],
        })
        self.assertEqual(analyzed.status_code, 200, analyzed.text)
        self.assertIsNone(analyzed.json()["consistency_score"])

        legacy = self.client.post("/api/live-session", json={"player_id": "player-1", "overall_score": 60})
        self.assertEqual(legacy.status_code, 200, legacy.text)
        history = self.client.get("/api/history/player-1").json()
        session_ids = {item["id"] for item in history}
        comparison = self.client.get("/api/comparison", params={"session_a": analyzed.json()["id"], "session_b": legacy.json()["id"]})
        self.assertEqual(comparison.status_code, 200, comparison.text)
        self.assertIn(analyzed.json()["id"], session_ids)
        self.assertEqual(comparison.json()["comparison"]["consistency_score"]["status"], "Unavailable")

    def test_live_repeated_mistake_requires_two_prior_occurrences(self):
        frames = [pose_frame() for _ in range(10)]
        for frame in frames:
            frame[12]["y"] = 0.8
            frame[24]["y"] = 0.2
        responses = [self.client.post("/api/live-session", json={
            "player_id": "player-1",
            "sport": "Cricket",
            "role": "Batter",
            "activity": "Batting",
            "duration_seconds": 8,
            "sampled_frames": 10,
            "pose_frames": frames,
        }) for _ in range(3)]
        self.assertTrue(all(response.status_code == 200 for response in responses))
        self.assertEqual(responses[0].json()["repeated_mistakes"], [])
        self.assertEqual(responses[1].json()["repeated_mistakes"], [])
        self.assertGreaterEqual(responses[2].json()["repeated_mistakes"][0]["sessions_affected"], 2)

    def test_video_analysis_keeps_existing_response_and_adds_profile_scores(self):
        class FakeVideoProcessor:
            total_frames = 300
            fps = 30

            def __init__(self, _path):
                pass

            def extract_frames(self, sample_every, limit):
                return list(range(10))

        class FakePoseEstimator:
            def __init__(self):
                self.pose = self

            def estimate_pose(self, index):
                return None, pose_frame(index * 0.002)

            def close(self):
                pass

        with patch.object(video_analysis, "validate_video", return_value=True), \
                patch.object(video_analysis, "VideoProcessor", FakeVideoProcessor), \
                patch.object(video_analysis, "PoseEstimator", FakePoseEstimator):
            response = self.client.post("/api/analyze", json={
                "player_id": "player-1",
                "sport": "Cricket",
                "role": "Batter",
                "activity": "Batting",
                "video_path": "synthetic.mp4",
            })

        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        for field in ("session_id", "player", "processing_pipeline", "analysis", "weaknesses", "repeated_mistakes", "prediction", "recommendations"):
            self.assertIn(field, result)
        self.assertIsNotNone(result["analysis"]["overall_score"])
        self.assertIn("role_adherence", result)
        self.assertIn("activity_performance", result)
        self.assertIn("data_quality", result)


if __name__ == "__main__":
    unittest.main()