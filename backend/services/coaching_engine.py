class CoachingEngine:
    def generate_recommendations(self, weaknesses: list, repeated_mistakes: list, prediction: dict):
        recommendations = []

        for weakness in weaknesses:
            feature = weakness.get("feature", "Technique")
            suggestion = weakness.get("suggested_improvement", "Keep practicing controlled movement.")
            reason = (
                "This recommendation is based on detected movement or stability issues "
                "in the current session and recent pattern analysis."
            )
            recommendations.append({
                "title": feature,
                "description": suggestion,
                "reason": reason,
            })

        if repeated_mistakes:
            recommendations.append({
                "title": "Repeat correction drill",
                "description": "Repeat the same controlled batting drill to reduce recurring session-to-session variation.",
                "reason": "A recurring issue was detected across multiple sessions.",
            })

        if prediction.get("trend", 0) < 0:
            recommendations.append({
                "title": "Trend recovery plan",
                "description": "Focus on technical reset drills that improve balance, posture, and movement consistency.",
                "reason": "Current performance trend is declining relative to recent sessions.",
            })

        return recommendations or [{
            "title": "Maintain current method",
            "description": "Continue the current routine and record another session to improve trend confidence.",
            "reason": "No major weaknesses were detected in the current analysis.",
        }]
