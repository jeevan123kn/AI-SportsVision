class MistakeDetector:
    def detect(self, history: list, current_weaknesses: list):
        recurring = []
        if not history:
            return recurring

        history_weaknesses = []
        for session in history:
            for item in session.get("weaknesses", []):
                history_weaknesses.append(item.get("feature"))

        for weakness in current_weaknesses:
            feature = weakness.get("feature")
            if feature and history_weaknesses.count(feature) >= 2:
                recurring.append({
                    "feature": feature,
                    "issue": weakness.get("issue"),
                    "sessions_affected": history_weaknesses.count(feature),
                    "trend": "Repeated pattern detected",
                })

        return recurring
