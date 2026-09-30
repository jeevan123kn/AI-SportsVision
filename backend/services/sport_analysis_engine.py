from __future__ import annotations

import math
import statistics

from services.sport_configs import DEFAULT_COMPONENT_WEIGHTS, get_named_weights, get_sport_config

TRACKED_LANDMARKS = (0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)
LIMB_TRACKS = ((13, 15), (14, 16), (25, 27), (26, 28))


def _clamp_score(value):
    return max(0.0, min(100.0, float(value)))


def _average_available(values, weights=None):
    selected = [(float(value), float(weights.get(key, 1.0) if weights else 1.0)) for key, value in values.items() if value is not None and (not weights or weights.get(key, 0) > 0)]
    total = sum(weight for _, weight in selected)
    return sum(value * weight for value, weight in selected) / total if total else None


def calculate_alignment_score(metrics):
    return _average_available(metrics, {"shoulder_alignment": 0.22, "hip_alignment": 0.22, "trunk_alignment": 0.24, "knee_alignment": 0.16, "body_symmetry": 0.16})


def calculate_posture_score(metrics):
    return _average_available({"alignment": calculate_alignment_score(metrics), "head_control": metrics.get("head_control")}, {"alignment": 0.78, "head_control": 0.22})


def calculate_balance_score(metrics):
    return _average_available(metrics, {"base_balance": 0.30, "shoulder_alignment": 0.16, "hip_alignment": 0.18, "trunk_alignment": 0.14, "body_symmetry": 0.12, "ankle_stability": 0.10})


def calculate_stability_score(metrics):
    temporal = _average_available(metrics, {"head_control": 0.35, "trunk_stability": 0.35, "ankle_stability": 0.20, "posture_consistency": 0.10})
    return temporal if temporal is not None else calculate_posture_score(metrics)


def calculate_consistency_score(metrics):
    return _average_available(metrics, {"posture_consistency": 0.60, "movement_consistency": 0.40})


def calculate_movement_score(metrics, pose_scores):
    movement_estimate = _average_available(metrics, {"motion_smoothness": 0.55, "movement_coordination": 0.25, "movement_consistency": 0.20})
    if movement_estimate is not None:
        return movement_estimate, "Estimated from movement"
    pose_proxy = _average_available(pose_scores, {"technique": 0.35, "balance": 0.30, "stability": 0.20, "consistency": 0.15})
    return pose_proxy, "Estimated from pose"


def calculate_role_adherence(component_scores, role_weights):
    return SportAnalysisEngine._weighted_score(component_scores, role_weights)


def calculate_activity_performance(component_scores, activity_weights):
    return SportAnalysisEngine._weighted_score(component_scores, activity_weights)


class PoseSequenceMetrics:
    visibility_threshold = 0.3

    @classmethod
    def point(cls, frame, index):
        if index >= len(frame) or not isinstance(frame[index], dict):
            return None
        point = frame[index]
        try:
            x = float(point["x"])
            y = float(point["y"])
            visibility = float(point.get("visibility", 0.0))
        except (KeyError, TypeError, ValueError):
            return None
        if visibility < cls.visibility_threshold or not math.isfinite(x) or not math.isfinite(y):
            return None
        return {"x": x, "y": y, "visibility": visibility}

    @classmethod
    def frame_is_usable(cls, frame):
        if not isinstance(frame, list) or len(frame) < 29:
            return False
        visible = {index for index in TRACKED_LANDMARKS if cls.point(frame, index) is not None}
        has_shoulders = 11 in visible and 12 in visible
        has_hips = 23 in visible and 24 in visible
        return len(visible) >= 4 and (has_shoulders or has_hips)

    @classmethod
    def measure(cls, frames):
        per_frame = []
        visibility_values = []
        visible_count = 0
        for frame in frames:
            points = {index: cls.point(frame, index) for index in TRACKED_LANDMARKS}
            visible_points = [point for point in points.values() if point is not None]
            if not visible_points:
                continue
            visibility_values.extend(point["visibility"] for point in visible_points)
            visible_count += len(visible_points)
            shoulder_center = SportAnalysisEngine._midpoint(points[11], points[12]) if points[11] and points[12] else None
            hip_center = SportAnalysisEngine._midpoint(points[23], points[24]) if points[23] and points[24] else None
            shoulder_width = SportAnalysisEngine._distance(points[11], points[12]) if shoulder_center else None
            hip_width = SportAnalysisEngine._distance(points[23], points[24]) if hip_center else None
            torso_scale = SportAnalysisEngine._distance(shoulder_center, hip_center) if shoulder_center and hip_center else max(shoulder_width or 0, hip_width or 0, 0.08)
            torso_scale = max(torso_scale, shoulder_width or 0, hip_width or 0, 0.08)
            center = hip_center or shoulder_center
            features = {}

            if shoulder_center:
                features["shoulder_alignment"] = SportAnalysisEngine._deviation_score(abs(points[11]["y"] - points[12]["y"]) / max(shoulder_width or 0, 0.01), 0.35)
            if hip_center:
                features["hip_alignment"] = SportAnalysisEngine._deviation_score(abs(points[23]["y"] - points[24]["y"]) / max(hip_width or 0, 0.01), 0.35)
            if shoulder_center and hip_center:
                trunk_offset = ((shoulder_center[0] - hip_center[0]) / torso_scale, (shoulder_center[1] - hip_center[1]) / torso_scale)
                features["trunk_alignment"] = SportAnalysisEngine._deviation_score(abs(trunk_offset[0]), 0.65)
            else:
                trunk_offset = None

            if points[0] and shoulder_center:
                head_offset = ((points[0]["x"] - shoulder_center[0]) / torso_scale, (points[0]["y"] - shoulder_center[1]) / torso_scale)
                features["head_position"] = SportAnalysisEngine._deviation_score(abs(head_offset[0]), 0.35)
            else:
                head_offset = None

            ankle_center = SportAnalysisEngine._midpoint(points[27], points[28]) if points[27] and points[28] else None
            stance_width = abs(points[27]["x"] - points[28]["x"]) if ankle_center else None
            if hip_center and ankle_center and stance_width is not None and stance_width >= 0.01:
                features["base_balance"] = SportAnalysisEngine._deviation_score(abs(hip_center[0] - ankle_center[0]) / stance_width, 0.75)

            knee_angles = [cls._joint_angle(points[hip], points[knee], points[ankle]) for hip, knee, ankle in ((23, 25, 27), (24, 26, 28))]
            knee_angles = [angle for angle in knee_angles if angle is not None]
            if len(knee_angles) == 2:
                features["knee_alignment"] = _clamp_score(100 - abs(knee_angles[0] - knee_angles[1]) / 120 * 100)
            elbow_angles = [cls._joint_angle(points[shoulder], points[elbow], points[wrist]) for shoulder, elbow, wrist in ((11, 13, 15), (12, 14, 16))]
            elbow_angles = [angle for angle in elbow_angles if angle is not None]
            if len(elbow_angles) == 2:
                features["arm_symmetry"] = _clamp_score(100 - abs(elbow_angles[0] - elbow_angles[1]) / 150 * 100)

            symmetry_signals = [features.get(key) for key in ("shoulder_alignment", "hip_alignment", "knee_alignment", "arm_symmetry") if features.get(key) is not None]
            if symmetry_signals:
                features["body_symmetry"] = statistics.fmean(symmetry_signals)

            positions = {}
            if center:
                for index, point in points.items():
                    if point:
                        positions[index] = ((point["x"] - center[0]) / torso_scale, (point["y"] - center[1]) / torso_scale)
            per_frame.append({"features": features, "positions": positions, "head_offset": head_offset, "trunk_offset": trunk_offset, "ankle_offset": ((ankle_center[0] - hip_center[0]) / torso_scale, (ankle_center[1] - hip_center[1]) / torso_scale) if ankle_center and hip_center else None, "stance_width": stance_width / max(hip_width or torso_scale, 0.01) if stance_width is not None else None, "torso_scale": torso_scale})

        if not per_frame:
            return {"metrics": {}, "values": {}, "observations": {}, "mean_visibility": 0.0, "landmark_completeness": 0.0, "usable_pose_frames": 0}

        observations = {}
        values = {}
        feature_names = set().union(*(frame["features"].keys() for frame in per_frame))
        for name in feature_names:
            samples = [frame["features"][name] for frame in per_frame if name in frame["features"]]
            if samples:
                values[name] = statistics.fmean(samples)
                observations[name] = len(samples)

        head_offsets = [frame["head_offset"] for frame in per_frame if frame["head_offset"] is not None]
        if len(head_offsets) >= 2:
            values["head_control"] = statistics.fmean((SportAnalysisEngine._temporal_score([item[axis] for item in head_offsets], 0.16) or 0.0) for axis in (0, 1))
            observations["head_control"] = len(head_offsets)
        elif "head_position" in values:
            values["head_control"] = values["head_position"]
            observations["head_control"] = observations["head_position"]

        trunk_offsets = [frame["trunk_offset"] for frame in per_frame if frame["trunk_offset"] is not None]
        if len(trunk_offsets) >= 2:
            values["trunk_stability"] = statistics.fmean((SportAnalysisEngine._temporal_score([item[axis] for item in trunk_offsets], 0.14) or 0.0) for axis in (0, 1))
            observations["trunk_stability"] = len(trunk_offsets)
        elif "trunk_alignment" in values:
            values["trunk_stability"] = values["trunk_alignment"]
            observations["trunk_stability"] = observations["trunk_alignment"]

        ankle_offsets = [frame["ankle_offset"] for frame in per_frame if frame["ankle_offset"] is not None]
        if len(ankle_offsets) >= 2:
            values["ankle_stability"] = statistics.fmean((SportAnalysisEngine._temporal_score([item[axis] for item in ankle_offsets], 0.20) or 0.0) for axis in (0, 1))
            observations["ankle_stability"] = len(ankle_offsets)
        elif "base_balance" in values:
            values["ankle_stability"] = values["base_balance"]
            observations["ankle_stability"] = observations["base_balance"]

        posture_samples = [_average_available(frame["features"], {"shoulder_alignment": 0.25, "hip_alignment": 0.25, "trunk_alignment": 0.25, "knee_alignment": 0.15, "body_symmetry": 0.10}) for frame in per_frame]
        posture_samples = [value for value in posture_samples if value is not None]
        if len(posture_samples) >= 2:
            values["posture_consistency"] = SportAnalysisEngine._temporal_score(posture_samples, 20.0)
            observations["posture_consistency"] = len(posture_samples)

        motion = cls._movement_metrics(per_frame)
        values.update({key: value for key, value in motion.items() if value is not None and key != "movement_range"})
        observations.update({key: len(per_frame) for key, value in motion.items() if value is not None})

        sources = {key: "Estimated from movement" if key in ("motion_smoothness", "movement_coordination", "movement_consistency") else "Estimated from pose" for key in values}
        details = {
            key: {"score": round(value, 1), "source": sources[key], "availability": "estimated", "basis": cls._basis(key)}
            for key, value in values.items()
        }
        if motion.get("movement_range") is not None:
            details["movement_range"] = {"score": None, "value": round(motion["movement_range"], 3), "unit": "torso lengths", "source": "Measured", "availability": "measured", "basis": "Mean normalized range of visible wrists, knees, and ankles across the sequence."}

        mean_visibility = statistics.fmean(visibility_values) if visibility_values else 0.0
        completeness = visible_count / (len(per_frame) * len(TRACKED_LANDMARKS)) if per_frame else 0.0
        return {"metrics": details, "values": values, "sources": sources, "observations": observations, "mean_visibility": mean_visibility, "landmark_completeness": completeness, "usable_pose_frames": len(per_frame)}

    @classmethod
    def _movement_metrics(cls, per_frame):
        transitions = []
        joint_paths = {index: [] for index in (13, 14, 15, 16, 25, 26, 27, 28)}
        for frame in per_frame:
            for index in joint_paths:
                if index in frame["positions"]:
                    joint_paths[index].append(frame["positions"][index])
        for first, second in zip(per_frame, per_frame[1:]):
            displacements = [
                math.dist(first["positions"][index], second["positions"][index])
                for index in joint_paths
                if index in first["positions"] and index in second["positions"]
            ]
            if displacements:
                transitions.append(statistics.fmean(displacements))

        path_ranges = []
        for path in joint_paths.values():
            if len(path) >= 2:
                path_ranges.append(max(math.dist(first, second) for first in path for second in path))
        movement_range = statistics.fmean(path_ranges) if path_ranges else None
        if not transitions or sum(transitions) < 0.005:
            return {"movement_range": movement_range}

        mean_motion = statistics.fmean(transitions)
        acceleration = [abs(second - first) for first, second in zip(transitions, transitions[1:])]
        smoothness = None
        consistency = None
        if acceleration:
            normalized_jerk = statistics.fmean(acceleration) / max(mean_motion, 0.005)
            smoothness = _clamp_score(100 - min(normalized_jerk, 1.0) * 100)
        if len(transitions) >= 2:
            coefficient = statistics.pstdev(transitions) / max(mean_motion, 0.005)
            consistency = _clamp_score(100 - min(coefficient, 1.5) / 1.5 * 100)

        pair_scores = []
        for left, right in ((15, 16), (27, 28), (25, 26)):
            if len(joint_paths[left]) >= 2 and len(joint_paths[right]) >= 2:
                left_range = max(math.dist(first, second) for first in joint_paths[left] for second in joint_paths[left])
                right_range = max(math.dist(first, second) for first in joint_paths[right] for second in joint_paths[right])
                pair_scores.append(_clamp_score(100 - abs(left_range - right_range) / max(left_range, right_range, 0.01) * 100))
        coordination = statistics.fmean(pair_scores) if pair_scores else None
        return {"motion_smoothness": smoothness, "movement_coordination": coordination, "movement_consistency": consistency, "movement_range": movement_range}

    @staticmethod
    def _joint_angle(first, middle, last):
        if not first or not middle or not last:
            return None
        first_vector = (first["x"] - middle["x"], first["y"] - middle["y"])
        last_vector = (last["x"] - middle["x"], last["y"] - middle["y"])
        denominator = math.hypot(*first_vector) * math.hypot(*last_vector)
        if denominator <= 1e-8:
            return None
        cosine = sum(left * right for left, right in zip(first_vector, last_vector)) / denominator
        return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))

    @staticmethod
    def _basis(name):
        return {
            "shoulder_alignment": "Shoulder height symmetry normalized by visible shoulder width.",
            "hip_alignment": "Hip height symmetry normalized by visible hip width.",
            "trunk_alignment": "Shoulder-to-hip center lean in the image plane.",
            "base_balance": "Hip center position relative to the visible ankle base.",
            "knee_alignment": "Left/right knee-angle symmetry from hip, knee, and ankle landmarks.",
            "arm_symmetry": "Left/right elbow-angle symmetry from shoulder, elbow, and wrist landmarks.",
            "body_symmetry": "Mean of the available shoulder, hip, knee, and arm symmetry signals.",
            "head_control": "Head position relative to the shoulder line across frames, or pose alignment in a single frame.",
            "trunk_stability": "Frame-to-frame variation of shoulder center relative to hip center.",
            "ankle_stability": "Frame-to-frame variation of the ankle base relative to the hip center.",
            "posture_consistency": "Variation in pose-derived alignment across the analyzed sequence.",
            "motion_smoothness": "Normalized frame-to-frame joint displacement and acceleration variation.",
            "movement_coordination": "Left/right wrist, knee, and ankle movement-range symmetry where both sides are visible.",
            "movement_consistency": "Variation in normalized joint displacement across consecutive frames.",
        }.get(name, "Derived from visible MediaPipe pose landmarks.")


class SportAnalysisEngine:
    def analyze(self, sport: str, role: str | None, activity: str | None, pose_frames: list, sampled_frames: int | None = None, duration_seconds: float | None = None):
        config = get_sport_config(sport)
        config = config or {"roles": [], "activities": [], "scoring_weights": DEFAULT_COMPONENT_WEIGHTS}
        valid_frames = [frame for frame in pose_frames or [] if PoseSequenceMetrics.frame_is_usable(frame)]
        attempted_frames = max(int(sampled_frames or 0), len(pose_frames or []), 1)
        pose_detection_rate = round(len(valid_frames) / attempted_frames * 100, 1)
        if not valid_frames:
            result = self._unavailable(sport, role, activity, "Insufficient visual data for reliable analysis.")
            result["data_quality"].update({"valid_frames": 0, "sampled_frames": attempted_frames, "pose_detection_rate": pose_detection_rate, "duration_seconds": duration_seconds})
            return result

        signals = PoseSequenceMetrics.measure(valid_frames)
        component_scores = self._components(signals)
        role_valid = self._contains(config.get("roles", []), role)
        activity_valid = self._contains(config.get("activities", []), activity)
        role_weights = get_named_weights(config, "role", role or "") or DEFAULT_COMPONENT_WEIGHTS
        activity_weights = get_named_weights(config, "activity", activity or "") or DEFAULT_COMPONENT_WEIGHTS
        role_score = calculate_role_adherence(component_scores, role_weights) if role_valid else None
        activity_score = calculate_activity_performance(component_scores, activity_weights) if activity_valid else None

        overall_weights = dict(config.get("scoring_weights", {}))
        weighted_values = {**component_scores, "role_adherence": role_score, "activity_performance": activity_score}
        overall_score, applied_weights, weighted_contributions = self._score_with_contributions(weighted_values, overall_weights)
        confidence = self._confidence(valid_frames, attempted_frames, signals, duration_seconds)
        for name, detail in signals["metrics"].items():
            observations = signals["observations"].get(name, len(valid_frames))
            detail["confidence"] = round(confidence * min(1.0, observations / max(1, min(8, len(valid_frames)))), 1)

        component_sources = self._component_sources(signals, component_scores)
        role_coverage = self._profile_coverage(component_scores, role_weights)
        activity_coverage = self._profile_coverage(component_scores, activity_weights)
        role_source = self._profile_source(role_weights, component_sources)
        activity_source = self._profile_source(activity_weights, component_sources)
        role_result = self._score_result(role_score, role_valid, f"{role or 'Selected role'} movement-profile alignment estimated from visible pose and movement characteristics; this does not prove skill execution.", role or "Selected role", confidence * role_coverage / 100, role_source)
        activity_explanation = "Pose-based movement proxy only; it does not verify skill outcome, contact, accuracy, speed, or task result."
        if sport.casefold() == "swimming":
            activity_explanation = "Visible-landmark posture proxy only. Underwater body mechanics, stroke phase, drag, and propulsion are unavailable from the current camera view."
        activity_result = self._score_result(activity_score, activity_valid, activity_explanation, activity or "Selected activity", confidence * activity_coverage / 100, activity_source)
        self._add_profile_evidence(role_result, role_weights, component_scores, f"{role or 'Selected'} role")
        self._add_profile_evidence(activity_result, activity_weights, component_scores, f"{activity or 'Selected'} activity")
        strengths, weaknesses = self._insights(signals, sport, activity, component_scores, component_sources)
        analysis_text = self._explanation(sport, role, activity, overall_score, component_scores, role_result, activity_result)
        available_weight = sum(weight for key, weight in overall_weights.items() if weighted_values.get(key) is not None)
        configured_weight = sum(overall_weights.values())
        score_coverage = round(available_weight / configured_weight * 100, 1) if configured_weight else 0.0
        status = "Pose-based estimates generated; interpret alongside confidence and score coverage."

        return {
            "overall_score": round(overall_score, 1) if overall_score is not None else None,
            "performance_level": self.performance_level(overall_score),
            "score_source": self._profile_source(applied_weights, component_sources),
            "role_adherence": role_result,
            "activity_performance": activity_result,
            "score_coverage": score_coverage,
            "role_weights": role_weights,
            "activity_weights": activity_weights,
            "component_scores": {key: round(value, 1) if value is not None else None for key, value in component_scores.items()},
            "component_sources": component_sources,
            "technique_score": component_scores.get("technique"),
            "balance_score": component_scores.get("balance"),
            "movement_score": component_scores.get("movement"),
            "consistency_score": component_scores.get("consistency"),
            "stability_score": component_scores.get("stability"),
            "confidence": confidence,
            "data_quality": {
                "valid_frames": len(valid_frames),
                "sampled_frames": attempted_frames,
                "pose_detection_rate": pose_detection_rate,
                "mean_landmark_visibility": round(signals["mean_visibility"] * 100, 1),
                "landmark_completeness": round(signals["landmark_completeness"] * 100, 1),
                "duration_seconds": round(float(duration_seconds), 2) if duration_seconds is not None else None,
                "score_coverage": score_coverage,
                "confidence": confidence,
            },
            "metrics": signals["metrics"],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "ai_analysis": analysis_text,
            "sport_profile": {"sport": sport, "role": role, "activity": activity, "status": status},
            "status": status,
            "weights": applied_weights,
            "configured_weights": overall_weights,
            "weighted_contributions": weighted_contributions,
        }

    @staticmethod
    def performance_level(score: float | None):
        if score is None:
            return "Insufficient data"
        if score >= 90:
            return "Elite"
        if score >= 80:
            return "Advanced"
        if score >= 70:
            return "Good"
        if score >= 60:
            return "Developing"
        return "Needs Improvement"

    @staticmethod
    def _contains(options: list, value: str | None):
        return bool(value) and any(option.casefold() == value.strip().casefold() for option in options)

    @staticmethod
    def _frame_is_usable(frame):
        return PoseSequenceMetrics.frame_is_usable(frame)

    def _measure(self, frames: list):
        return PoseSequenceMetrics.measure(frames)

    @staticmethod
    def _metric_basis(name: str):
        return {
            "head_control": "Variation in nose position relative to the shoulder line across visible frames.",
            "shoulder_alignment": "Image-plane shoulder height difference normalized by shoulder width.",
            "hip_alignment": "Image-plane hip height difference normalized by hip width.",
            "trunk_alignment": "Horizontal shoulder-to-hip center offset normalized by shoulder width.",
            "base_balance": "Hip center position relative to the visible ankle span in the image plane.",
            "trunk_stability": "Variation in torso center offset relative to hip center across frames.",
            "posture_consistency": "Variation in the measured alignment signals across usable frames.",
        }.get(name, "Derived from visible pose landmarks.")

    @staticmethod
    def _components(signals: dict):
        values = signals.get("values", {})
        technique = calculate_posture_score(values)
        balance = calculate_balance_score(values)
        stability = calculate_stability_score(values)
        consistency = calculate_consistency_score(values)
        movement, _ = calculate_movement_score(values, {"technique": technique, "balance": balance, "stability": stability, "consistency": consistency})
        return {"technique": technique, "balance": balance, "movement": movement, "consistency": consistency, "stability": stability}

    @staticmethod
    def _component_sources(signals, component_scores):
        values = signals.get("values", {})
        movement_source = calculate_movement_score(values, component_scores)[1]
        sources = {
            "technique": "Estimated from pose",
            "balance": "Estimated from pose",
            "movement": movement_source,
            "consistency": "Estimated from movement" if values.get("movement_consistency") is not None else "Estimated from pose",
            "stability": "Estimated from movement" if values.get("trunk_stability") is not None or values.get("ankle_stability") is not None else "Estimated from pose",
        }
        return {key: source if component_scores.get(key) is not None else "Insufficient data" for key, source in sources.items()}

    @staticmethod
    def _profile_coverage(component_scores, weights):
        total = sum(weights.values())
        return sum(weight for key, weight in weights.items() if component_scores.get(key) is not None) / total * 100 if total else 0.0

    @staticmethod
    def _profile_source(weights, sources):
        movement_weight = weights.get("movement", 0.0) + weights.get("consistency", 0.0) + weights.get("stability", 0.0)
        movement_source = any(sources.get(key) == "Estimated from movement" and weights.get(key, 0.0) >= 0.1 for key in ("movement", "consistency", "stability"))
        return "Estimated from movement" if movement_source and movement_weight >= 0.2 else "Estimated from pose"

    @staticmethod
    def _weighted_score(values: dict, weights: dict):
        selected = [(float(values[key]), float(weight)) for key, weight in weights.items() if key in values and values[key] is not None and weight > 0]
        total_weight = sum(weight for _, weight in selected)
        return sum(value * weight for value, weight in selected) / total_weight if total_weight else None

    @staticmethod
    def _score_with_contributions(values: dict, weights: dict):
        selected = {key: float(weight) for key, weight in weights.items() if values.get(key) is not None and weight > 0}
        total_weight = sum(selected.values())
        if not total_weight:
            return None, {}, {}
        normalized = {key: weight / total_weight for key, weight in selected.items()}
        contributions = {
            key: {"score": round(float(values[key]), 1), "weight": round(normalized[key], 4), "points": round(float(values[key]) * normalized[key], 2)}
            for key in normalized
        }
        return sum(item["points"] for item in contributions.values()), normalized, contributions

    @staticmethod
    def _add_profile_evidence(result: dict, weights: dict, component_scores: dict, profile_name: str):
        if result.get("score") is None:
            return
        contributors = {key: score for key, score in component_scores.items() if key in weights and score is not None}
        result["contributing_scores"] = contributors
        result["strengths"] = [f"{key.replace('_', ' ').title()} movement proxy: {score:.0f}/100." for key, score in contributors.items() if score >= 80]
        result["weaknesses"] = [f"{key.replace('_', ' ').title()} movement proxy: {score:.0f}/100 (profile weight {weights[key] * 100:.0f}%)." for key, score in contributors.items() if score < 60]
        result["recommendations"] = [
            f"Practice a controlled {profile_name} drill focused on {key.replace('_', ' ')} and review the next recorded sequence."
            for key, score in contributors.items()
            if score < 60
        ]
        strongest = max(contributors, key=contributors.get) if contributors else None
        lowest = min(contributors, key=contributors.get) if contributors else None
        if strongest and lowest and strongest != lowest:
            result["analysis"] += f" {profile_name} movement-profile estimate is {result['score']:.0f}/100. {strongest.replace('_', ' ')} is strongest ({contributors[strongest]:.0f}/100); {lowest.replace('_', ' ')} is the lowest measured contributor ({contributors[lowest]:.0f}/100). Sport-skill outcome is not inferred."
        result["score_coverage"] = round(SportAnalysisEngine._profile_coverage(component_scores, weights), 1)

    @staticmethod
    def _score_result(score, supported: bool, explanation: str, selected: str, confidence: float, source: str):
        if not supported or score is None:
            reason = "Selected role or activity is not present in the configured profile." if not supported else "Insufficient pose or movement signals for this estimate."
            return {"score": None, "confidence": round(confidence, 1), "source": "Insufficient data", "status": "Insufficient data", "analysis": reason, "selected": selected, "availability": "insufficient_data", "score_coverage": 0.0}
        return {"score": round(score, 1), "confidence": round(confidence, 1), "source": source, "status": SportAnalysisEngine.performance_level(score), "analysis": explanation, "selected": selected, "availability": "estimated", "score_coverage": 100.0}

    @staticmethod
    def _confidence(frames, attempted, signals, duration):
        detection = min(1.0, len(frames) / max(attempted, 1))
        visibility = signals.get("mean_visibility", 0.0)
        completeness = signals.get("landmark_completeness", 0.0)
        frame_adequacy = min(1.0, len(frames) / 12)
        duration_adequacy = min(1.0, max(float(duration or 0), 0) / 8)
        parts = [(detection, 0.28), (visibility, 0.24), (completeness, 0.16), (frame_adequacy, 0.20)]
        if duration is not None:
            parts.append((duration_adequacy, 0.12))
        total_weight = sum(weight for _, weight in parts)
        return round(sum(value * weight for value, weight in parts) / total_weight * 100, 1)

    @staticmethod
    def _insights(signals: dict, sport: str, activity: str | None, components: dict, sources: dict):
        strengths = []
        weaknesses = []
        labels = {"technique": "Technique", "balance": "Balance", "movement": "Movement quality", "consistency": "Movement consistency", "stability": "Stability"}
        for key, value in components.items():
            if value is None:
                continue
            label = labels[key]
            if value >= 80:
                strengths.append(f"{label} is a strength ({value:.0f}/100; {sources.get(key, 'Estimated from pose')}).")
            elif value < 60:
                metric_values = signals.get("values", {})
                evidence_keys = [name for name, score in metric_values.items() if score is not None and score < 65]
                evidence = ", ".join(f"{name.replace('_', ' ')} {metric_values[name]:.0f}/100" for name in evidence_keys[:3]) or f"{key}={value:.1f}/100"
                weaknesses.append({"feature": label, "issue": f"{label} estimate is among the lowest supported movement measures.", "severity": "Medium" if value >= 40 else "High", "evidence": evidence, "impact": f"May reduce movement control during the observed {activity or sport} sequence; skill outcome is not measured.", "suggested_improvement": f"Review {label.lower()} during controlled {activity or sport} practice and compare another recorded sequence."})
        return strengths[:5], weaknesses[:5]

    @staticmethod
    def _explanation(sport, role, activity, overall, components, role_result, activity_result):
        available = {key: value for key, value in components.items() if value is not None}
        ordered = sorted(available.items(), key=lambda item: item[1], reverse=True)
        best = f"{ordered[0][0]} is strongest at {ordered[0][1]:.0f}/100" if ordered else "pose data is limited"
        lowest = f"{ordered[-1][0]} is lowest at {ordered[-1][1]:.0f}/100" if len(ordered) > 1 else ""
        role_text = f" Role adherence is {role_result['score']:.0f}/100 ({role_result['confidence']:.0f}% confidence)." if role_result.get("score") is not None else " Role adherence has insufficient data."
        activity_text = f" Activity movement estimate is {activity_result['score']:.0f}/100 ({activity_result['confidence']:.0f}% confidence)." if activity_result.get("score") is not None else " Activity performance has insufficient data."
        comparison = f"; {lowest}" if lowest else ""
        overall_text = f"Overall movement-profile estimate is {overall:.0f}/100" if overall is not None else "Overall score has insufficient data"
        return f"{sport} {role or 'role'} / {activity or 'activity'} analysis: {overall_text}; {best}{comparison}.{role_text}{activity_text} Scores estimate visible movement patterns, not equipment contact, accuracy, speed, or task outcomes."

    @staticmethod
    def _unavailable(sport, role, activity, reason):
        return {"overall_score": None, "score_source": "Insufficient data", "performance_level": "Insufficient data", "role_adherence": {"score": None, "confidence": 0.0, "source": "Insufficient data", "status": "Insufficient data", "analysis": reason, "selected": role, "availability": "insufficient_data"}, "activity_performance": {"score": None, "confidence": 0.0, "source": "Insufficient data", "status": "Insufficient data", "analysis": reason, "selected": activity, "availability": "insufficient_data"}, "component_scores": {"technique": None, "balance": None, "movement": None, "consistency": None, "stability": None}, "component_sources": {}, "confidence": 0.0, "score_coverage": 0.0, "data_quality": {"valid_frames": 0, "sampled_frames": 0, "pose_detection_rate": 0.0, "mean_landmark_visibility": 0.0, "landmark_completeness": 0.0, "duration_seconds": None, "score_coverage": 0.0, "confidence": 0.0}, "metrics": {}, "strengths": [], "weaknesses": [], "ai_analysis": reason, "sport_profile": {"sport": sport, "role": role, "activity": activity, "status": reason}, "status": reason, "weights": {}, "weighted_contributions": {}}

    @staticmethod
    def _distance(first, second):
        first_x, first_y = (first["x"], first["y"]) if isinstance(first, dict) else first
        second_x, second_y = (second["x"], second["y"]) if isinstance(second, dict) else second
        return math.hypot(first_x - second_x, first_y - second_y)

    @staticmethod
    def _midpoint(first, second):
        return ((first["x"] + second["x"]) / 2, (first["y"] + second["y"]) / 2)

    @staticmethod
    def _deviation_score(deviation, tolerance):
        return max(0.0, min(100.0, (1 - deviation / tolerance) * 100))

    @staticmethod
    def _temporal_score(values, tolerance):
        if len(values) < 2:
            return None
        return max(0.0, min(100.0, 100 - statistics.pstdev(values) / max(tolerance, 1e-5) * 100))

