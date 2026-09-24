from __future__ import annotations


class PerformanceAnalyzer:
    def __init__(self):
        self.weights = {
            "technique": 0.30,
            "balance": 0.25,
            "movement": 0.20,
            "consistency": 0.15,
            "stability": 0.10,
        }

    def analyze(self, feature_metrics: dict):
        if not feature_metrics:
            return {
                "overall_score": 0.0,
                "component_scores": {},
                "status": "Insufficient data for performance analysis.",
            }

        technique = self._clamp((feature_metrics.get("head_stability", 0.5) * 55) + (feature_metrics.get("shoulder_alignment", 0.5) * 45))
        balance = self._clamp((feature_metrics.get("balance_score", 0.5) * 100))
        movement = self._clamp((feature_metrics.get("movement_score", 0.5) * 100))
        consistency = self._clamp((feature_metrics.get("movement_consistency", 0.5) * 100))
        stability = self._clamp((feature_metrics.get("stability_score", 0.5) * 100))

        component_scores = {
            "technique": round(technique, 2),
            "balance": round(balance, 2),
            "movement": round(movement, 2),
            "consistency": round(consistency, 2),
            "stability": round(stability, 2),
        }

        overall = (
            component_scores["technique"] * self.weights["technique"]
            + component_scores["balance"] * self.weights["balance"]
            + component_scores["movement"] * self.weights["movement"]
            + component_scores["consistency"] * self.weights["consistency"]
            + component_scores["stability"] * self.weights["stability"]
        )

        return {
            "overall_score": round(overall, 2),
            "component_scores": component_scores,
            "status": "Analysis generated from extracted motion features.",
            "weights": self.weights,
        }

    def _clamp(self, value):
        return max(0.0, min(100.0, float(value)))
