class WeaknessDetector:
    def detect(self, feature_metrics: dict):
        weaknesses = []
        if not feature_metrics:
            return weaknesses

        if feature_metrics.get("head_stability", 1.0) < 0.7:
            weaknesses.append({
                "feature": "Head stability",
                "issue": "Head movement during setup or swing is inconsistent",
                "severity": "Medium",
                "evidence": f"head_stability={feature_metrics.get('head_stability', 'n/a')}",
                "suggested_improvement": "Practice controlled batting drills while maintaining a stable head position.",
            })

        if feature_metrics.get("foot_movement", 0.0) > 0.25:
            weaknesses.append({
                "feature": "Foot movement",
                "issue": "Foot movement shows variation across frames",
                "severity": "Medium",
                "evidence": f"foot_movement={feature_metrics.get('foot_movement', 'n/a')}",
                "suggested_improvement": "Focus on controlled lower-body movement and repeat the stance-to-shot drill.",
            })

        if feature_metrics.get("balance_score", 1.0) < 0.7:
            weaknesses.append({
                "feature": "Balance",
                "issue": "Body balance is unstable during movement",
                "severity": "High",
                "evidence": f"balance_score={feature_metrics.get('balance_score', 'n/a')}",
                "suggested_improvement": "Work on a more stable base with deliberate weight transfer and stance control.",
            })

        if feature_metrics.get("movement_consistency", 1.0) < 0.7:
            weaknesses.append({
                "feature": "Technique consistency",
                "issue": "Movement pattern varies significantly between repetitions",
                "severity": "Medium",
                "evidence": f"movement_consistency={feature_metrics.get('movement_consistency', 'n/a')}",
                "suggested_improvement": "Repeat the same batting routine with a slower, controlled rhythm to improve consistency.",
            })

        return weaknesses
