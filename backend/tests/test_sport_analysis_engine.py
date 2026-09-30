import unittest

from services.sport_analysis_engine import SportAnalysisEngine
from services.sport_configs import SPORT_ANALYSIS_CONFIG


def pose_frame(offset=0.0):
    frame = [{"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.95} for _ in range(33)]
    frame[0].update(x=0.5 + offset, y=0.25)
    frame[11].update(x=0.4 + offset, y=0.4)
    frame[12].update(x=0.6 + offset, y=0.4)
    frame[23].update(x=0.44 + offset, y=0.65)
    frame[24].update(x=0.56 + offset, y=0.65)
    frame[25].update(x=0.44 + offset, y=0.8)
    frame[26].update(x=0.56 + offset, y=0.8)
    frame[27].update(x=0.4 + offset, y=0.95)
    frame[28].update(x=0.6 + offset, y=0.95)
    return frame


class SportAnalysisEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = SportAnalysisEngine()
        self.frames = [pose_frame(index * 0.002) for index in range(12)]

    def test_requested_sport_profiles_produce_deterministic_pose_scores(self):
        cases = [
            ("Cricket", "Batter", "Batting"),
            ("Cricket", "Bowler", "Bowling"),
            ("Football", "Defender", "Defending"),
            ("Basketball", "Point Guard", "Passing"),
            ("Tennis", "Singles", "Forehand"),
        ]
        for sport, role, activity in cases:
            with self.subTest(sport=sport, role=role, activity=activity):
                result = self.engine.analyze(sport, role, activity, self.frames, 12, 6.0)
                self.assertIsNotNone(result["overall_score"])
                self.assertEqual(result["role_adherence"]["availability"], "estimated")
                self.assertEqual(result["activity_performance"]["availability"], "estimated")
                self.assertGreater(result["confidence"], 0)
                self.assertIn("does not verify skill outcome", result["activity_performance"]["analysis"])
                self.assertAlmostEqual(sum(result["weights"].values()), 1.0)
                self.assertAlmostEqual(sum(item["points"] for item in result["weighted_contributions"].values()), result["overall_score"], places=1)

    def test_all_frontend_sports_are_configured(self):
        self.assertEqual(len(SPORT_ANALYSIS_CONFIG), 10)
        for sport, config in SPORT_ANALYSIS_CONFIG.items():
            with self.subTest(sport=sport):
                result = self.engine.analyze(sport, config["roles"][0], config["activities"][0], self.frames, 12, 6.0)
                self.assertIsNotNone(result["overall_score"])

    def test_no_pose_data_returns_no_fabricated_scores(self):
        result = self.engine.analyze("Cricket", "Batter", "Batting", [], 10, 2.0)
        self.assertIsNone(result["overall_score"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["strengths"], [])

    def test_motionless_sequence_gets_a_labeled_pose_movement_estimate(self):
        result = self.engine.analyze("Cricket", "Batter", "Batting", [pose_frame() for _ in range(10)], 10, 5.0)
        self.assertIsNotNone(result["movement_score"])
        self.assertGreaterEqual(result["movement_score"], 0)
        self.assertLessEqual(result["movement_score"], 100)
        self.assertEqual(result["component_sources"]["movement"], "Estimated from pose")

    def test_single_valid_frame_returns_low_confidence_pose_estimates(self):
        result = self.engine.analyze("Cricket", "Batter", "Batting", self.frames[:1], 10, 5.0)
        self.assertIsNotNone(result["overall_score"])
        self.assertLess(result["confidence"], 70)
        self.assertIsNone(result["component_scores"]["consistency"])

    def test_partial_landmark_visibility_keeps_supported_scores(self):
        frames = [pose_frame(index * 0.002) for index in range(6)]
        for frame in frames:
            for index in (13, 14, 15, 16, 25, 26, 27, 28):
                frame[index]["visibility"] = 0.1
        result = self.engine.analyze("Cricket", "Batter", "Batting", frames, 6, 3.0)
        self.assertIsNotNone(result["overall_score"])
        self.assertIsNotNone(result["role_adherence"]["score"])
        self.assertIsNotNone(result["activity_performance"]["score"])
        self.assertGreater(result["score_coverage"], 0)

    def test_wrist_and_ankle_tracks_produce_movement_estimates(self):
        frames = [pose_frame() for _ in range(8)]
        for index, frame in enumerate(frames):
            frame[15].update(x=0.45 + index * 0.012, y=0.5)
            frame[16].update(x=0.55 - index * 0.008, y=0.5)
            frame[27].update(x=0.4 + index * 0.006, y=0.95)
        result = self.engine.analyze("Cricket", "Batter", "Batting", frames, 8, 4.0)
        self.assertIsNotNone(result["movement_score"])
        self.assertEqual(result["component_sources"]["movement"], "Estimated from movement")
        self.assertEqual(result["metrics"]["movement_range"]["source"], "Measured")

    def test_activity_and_role_weights_change_with_selection(self):
        batting = self.engine.analyze("Cricket", "Batter", "Batting", self.frames, 12, 6.0)
        bowling = self.engine.analyze("Cricket", "Bowler", "Bowling", self.frames, 12, 6.0)
        self.assertNotEqual(batting["role_weights"], bowling["role_weights"])
        self.assertNotEqual(batting["activity_weights"], bowling["activity_weights"])

    def test_selected_role_activity_and_sport_change_scores(self):
        frames = [pose_frame() for _ in range(12)]
        changes = [0, 0.02, -0.04, 0.07, -0.03, 0.05, -0.06, 0.03, -0.02, 0.06, -0.04, 0.01]
        for frame, change in zip(frames, changes):
            frame[12]["y"] += change
            frame[24]["y"] += change * 0.7
            frame[27]["x"] += change * 0.4
            frame[28]["x"] -= change * 0.3
            frame[15]["x"] += change
            frame[16]["x"] -= change * 0.5

        batter_batting = self.engine.analyze("Cricket", "Batter", "Batting", frames, 12, 6.0)
        bowler_bowling = self.engine.analyze("Cricket", "Bowler", "Bowling", frames, 12, 6.0)
        batter_bowling = self.engine.analyze("Cricket", "Batter", "Bowling", frames, 12, 6.0)
        football_defender = self.engine.analyze("Football", "Defender", "Defending", frames, 12, 6.0)
        self.assertNotEqual(batter_batting["role_adherence"]["score"], bowler_bowling["role_adherence"]["score"])
        self.assertNotEqual(batter_batting["activity_performance"]["score"], batter_bowling["activity_performance"]["score"])
        self.assertNotEqual(batter_batting["overall_score"], football_defender["overall_score"])

    def test_unsupported_role_or_activity_is_excluded(self):
        result = self.engine.analyze("Football", "Batter", "Batting", self.frames, 12, 6.0)
        self.assertIsNone(result["role_adherence"]["score"])
        self.assertIsNone(result["activity_performance"]["score"])

    def test_swimming_does_not_claim_underwater_metrics(self):
        result = self.engine.analyze("Swimming", "Freestyle", "Freestyle", self.frames, 12, 6.0)
        self.assertIn("Underwater body mechanics", result["activity_performance"]["analysis"])

    def test_supported_profiles_are_explicit_for_every_option(self):
        for config in SPORT_ANALYSIS_CONFIG.values():
            self.assertTrue(all(role in config["role_weights"] for role in config["roles"]))
            self.assertTrue(all(activity in config["activity_weights"] for activity in config["activities"]))


if __name__ == "__main__":
    unittest.main()