class CoachingEngine:
    def generate_recommendations(self, weaknesses: list, repeated_mistakes: list, prediction: dict, sport="Cricket", role=None, activity=None):
        recommendations = []

        for weakness in weaknesses:
            feature = weakness.get("feature", "Technique")
            suggestion = weakness.get("suggested_improvement", "Keep practicing controlled movement.")
            reason = weakness.get("evidence") or "Based on a pose-derived movement signal from this session."
            recommendations.append({
                "title": feature,
                "description": suggestion,
                "reason": f"{reason} Selected focus: {sport} / {role or 'role not specified'} / {activity or 'activity not specified'}.",
            })

        if repeated_mistakes:
            recommendations.append({
                "title": "Repeat correction drill",
                "description": f"Repeat a controlled {activity or sport} drill that targets the recurring movement issue, then record another session to check for change.",
                "reason": "A recurring issue was detected across multiple sessions.",
            })

        if prediction.get("trend", 0) < 0:
            recommendations.append({
                "title": "Trend recovery plan",
                "description": f"Use a controlled {activity or sport} reset drill focused on the measured weakness, then reassess in a later session.",
                "reason": "Current performance trend is declining relative to recent sessions.",
            })

        return recommendations
