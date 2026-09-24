class PredictionEngine:
    def predict(self, history_scores: list[float], current_score: float):
        if len(history_scores) < 2:
            return {
                "current_performance": current_score,
                "previous_performance": history_scores[-1] if history_scores else 0.0,
                "trend": 0.0,
                "predicted_future_performance": current_score,
                "confidence": 0.0,
                "notes": "Insufficient historical sessions for prediction.",
            }

        previous = history_scores[-1]
        trend = current_score - previous
        predicted = current_score + (trend * 0.5)
        confidence = min(0.9, max(0.35, 0.4 + (len(history_scores) * 0.08)))

        return {
            "current_performance": round(current_score, 2),
            "previous_performance": round(previous, 2),
            "trend": round(trend, 2),
            "predicted_future_performance": round(predicted, 2),
            "confidence": round(confidence, 2),
            "notes": "Prediction is based on recent session trend and historical performance data.",
        }
