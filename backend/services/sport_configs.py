SPORT_ANALYSIS_CONFIG = {
    "Cricket": {
        "roles": ["Batter", "Bowler", "Wicketkeeper", "All-Rounder"],
        "activities": ["Batting", "Bowling", "Fielding", "Wicketkeeping"],
        "scoring_weights": {"technique": 0.20, "balance": 0.16, "movement": 0.12, "consistency": 0.12, "stability": 0.12, "role_adherence": 0.14, "activity_performance": 0.14},
        "role_weights": {
            "Batter": {"technique": 0.30, "balance": 0.22, "movement": 0.08, "consistency": 0.13, "stability": 0.27},
            "Bowler": {"technique": 0.24, "balance": 0.20, "movement": 0.22, "consistency": 0.18, "stability": 0.16},
            "Wicketkeeper": {"technique": 0.16, "balance": 0.28, "movement": 0.22, "consistency": 0.16, "stability": 0.18},
        },
        "activity_weights": {
            "Batting": {"technique": 0.34, "balance": 0.24, "movement": 0.08, "consistency": 0.14, "stability": 0.20},
            "Bowling": {"technique": 0.22, "balance": 0.20, "movement": 0.24, "consistency": 0.18, "stability": 0.16},
            "Fielding": {"technique": 0.12, "balance": 0.20, "movement": 0.32, "consistency": 0.18, "stability": 0.18},
            "Wicketkeeping": {"technique": 0.14, "balance": 0.30, "movement": 0.22, "consistency": 0.16, "stability": 0.18},
        },
        "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]},
    },
    "Football": {
        "roles": ["Goalkeeper", "Defender", "Midfielder", "Forward", "Winger"],
        "activities": ["Shooting", "Passing", "Dribbling", "Defending", "Goalkeeping"],
        "scoring_weights": {"technique": 0.14, "balance": 0.16, "movement": 0.18, "consistency": 0.12, "stability": 0.10, "role_adherence": 0.15, "activity_performance": 0.15},
        "role_weights": {"Goalkeeper": {"technique": 0.14, "balance": 0.26, "movement": 0.18, "consistency": 0.16, "stability": 0.26}, "Defender": {"technique": 0.12, "balance": 0.24, "movement": 0.20, "consistency": 0.18, "stability": 0.26}, "Midfielder": {"technique": 0.16, "balance": 0.18, "movement": 0.28, "consistency": 0.20, "stability": 0.18}, "Forward": {"technique": 0.20, "balance": 0.16, "movement": 0.28, "consistency": 0.18, "stability": 0.18}, "Winger": {"technique": 0.14, "balance": 0.18, "movement": 0.32, "consistency": 0.20, "stability": 0.16}},
        "activity_weights": {"Shooting": {"technique": 0.26, "balance": 0.20, "movement": 0.22, "consistency": 0.16, "stability": 0.18}, "Passing": {"technique": 0.20, "balance": 0.18, "movement": 0.24, "consistency": 0.22, "stability": 0.18}, "Dribbling": {"technique": 0.14, "balance": 0.22, "movement": 0.30, "consistency": 0.20, "stability": 0.16}, "Defending": {"technique": 0.12, "balance": 0.24, "movement": 0.24, "consistency": 0.18, "stability": 0.22}, "Goalkeeping": {"technique": 0.14, "balance": 0.26, "movement": 0.18, "consistency": 0.16, "stability": 0.26}},
        "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]},
    },
    "Basketball": {
        "roles": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
        "activities": ["Shooting", "Dribbling", "Passing", "Defense", "Rebounding"],
        "scoring_weights": {"technique": 0.16, "balance": 0.17, "movement": 0.15, "consistency": 0.12, "stability": 0.12, "role_adherence": 0.14, "activity_performance": 0.14},
        "role_weights": {"Point Guard": {"technique": 0.16, "balance": 0.16, "movement": 0.30, "consistency": 0.22, "stability": 0.16}, "Shooting Guard": {"technique": 0.26, "balance": 0.18, "movement": 0.20, "consistency": 0.20, "stability": 0.16}, "Small Forward": {"technique": 0.18, "balance": 0.18, "movement": 0.24, "consistency": 0.20, "stability": 0.20}, "Power Forward": {"technique": 0.16, "balance": 0.24, "movement": 0.18, "consistency": 0.18, "stability": 0.24}, "Center": {"technique": 0.14, "balance": 0.26, "movement": 0.16, "consistency": 0.18, "stability": 0.26}},
        "activity_weights": {"Shooting": {"technique": 0.28, "balance": 0.22, "movement": 0.14, "consistency": 0.20, "stability": 0.16}, "Dribbling": {"technique": 0.14, "balance": 0.20, "movement": 0.30, "consistency": 0.20, "stability": 0.16}, "Passing": {"technique": 0.22, "balance": 0.16, "movement": 0.22, "consistency": 0.22, "stability": 0.18}, "Defense": {"technique": 0.12, "balance": 0.24, "movement": 0.26, "consistency": 0.20, "stability": 0.18}, "Rebounding": {"technique": 0.14, "balance": 0.26, "movement": 0.20, "consistency": 0.18, "stability": 0.22}},
        "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]},
    },
    "Tennis": {
        "roles": ["Singles", "Doubles"],
        "activities": ["Serve", "Forehand", "Backhand", "Volley", "Footwork"],
        "scoring_weights": {"technique": 0.18, "balance": 0.18, "movement": 0.16, "consistency": 0.13, "stability": 0.11, "role_adherence": 0.12, "activity_performance": 0.12},
        "role_weights": {"Singles": {"technique": 0.18, "balance": 0.20, "movement": 0.26, "consistency": 0.20, "stability": 0.14}, "Doubles": {"technique": 0.22, "balance": 0.18, "movement": 0.22, "consistency": 0.22, "stability": 0.14}},
        "activity_weights": {"Serve": {"technique": 0.28, "balance": 0.18, "movement": 0.18, "consistency": 0.18, "stability": 0.18}, "Forehand": {"technique": 0.26, "balance": 0.18, "movement": 0.20, "consistency": 0.20, "stability": 0.16}, "Backhand": {"technique": 0.26, "balance": 0.18, "movement": 0.20, "consistency": 0.20, "stability": 0.16}, "Volley": {"technique": 0.22, "balance": 0.20, "movement": 0.22, "consistency": 0.18, "stability": 0.18}, "Footwork": {"technique": 0.10, "balance": 0.22, "movement": 0.30, "consistency": 0.22, "stability": 0.16}},
        "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]},
    },
    "Badminton": {"roles": ["Singles", "Doubles", "Mixed Doubles"], "activities": ["Serve", "Smash", "Drop Shot", "Clear", "Net Play", "Footwork"], "scoring_weights": {"technique": 0.15, "balance": 0.18, "movement": 0.19, "consistency": 0.13, "stability": 0.11, "role_adherence": 0.12, "activity_performance": 0.12}, "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]}},
    "Volleyball": {"roles": ["Setter", "Libero", "Outside Hitter", "Middle Blocker", "Opposite Hitter"], "activities": ["Serving", "Spiking", "Blocking", "Setting", "Digging"], "scoring_weights": {"technique": 0.18, "balance": 0.17, "movement": 0.15, "consistency": 0.12, "stability": 0.14, "role_adherence": 0.12, "activity_performance": 0.12}, "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]}},
    "Hockey": {"roles": ["Goalkeeper", "Defender", "Midfielder", "Forward"], "activities": ["Dribbling", "Passing", "Shooting", "Defending", "Goalkeeping"], "scoring_weights": {"technique": 0.14, "balance": 0.18, "movement": 0.18, "consistency": 0.13, "stability": 0.11, "role_adherence": 0.13, "activity_performance": 0.13}, "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]}},
    "Table Tennis": {"roles": ["Singles", "Doubles", "Mixed Doubles"], "activities": ["Serve", "Forehand", "Backhand", "Smash", "Footwork"], "scoring_weights": {"technique": 0.21, "balance": 0.17, "movement": 0.13, "consistency": 0.16, "stability": 0.14, "role_adherence": 0.10, "activity_performance": 0.09}, "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]}},
    "Athletics": {"roles": ["Sprinter", "Middle Distance", "Long Distance", "Hurdler", "Jumper", "Thrower", "All-Round Athlete"], "activities": ["Sprinting", "Distance Running", "Hurdles", "Long Jump", "High Jump", "Throwing"], "scoring_weights": {"technique": 0.19, "balance": 0.14, "movement": 0.20, "consistency": 0.16, "stability": 0.10, "role_adherence": 0.11, "activity_performance": 0.13}, "activity_weights": {"Sprinting": {"technique": 0.20, "balance": 0.12, "movement": 0.30, "consistency": 0.22, "stability": 0.16}, "Distance Running": {"technique": 0.18, "balance": 0.14, "movement": 0.24, "consistency": 0.28, "stability": 0.16}, "Hurdles": {"technique": 0.22, "balance": 0.18, "movement": 0.24, "consistency": 0.20, "stability": 0.16}, "Long Jump": {"technique": 0.22, "balance": 0.18, "movement": 0.24, "consistency": 0.18, "stability": 0.18}, "High Jump": {"technique": 0.22, "balance": 0.18, "movement": 0.22, "consistency": 0.18, "stability": 0.20}, "Throwing": {"technique": 0.26, "balance": 0.20, "movement": 0.18, "consistency": 0.20, "stability": 0.16}}, "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]}},
    "Swimming": {"roles": ["Freestyle", "Backstroke", "Breaststroke", "Butterfly", "Individual Medley"], "activities": ["Freestyle", "Backstroke", "Breaststroke", "Butterfly", "Individual Medley"], "scoring_weights": {"technique": 0.22, "balance": 0.15, "movement": 0.16, "consistency": 0.15, "stability": 0.10, "role_adherence": 0.11, "activity_performance": 0.11}, "metric_focus": {"technique": ["head_control", "shoulder_alignment", "hip_alignment", "trunk_alignment"], "balance": ["base_balance", "hip_alignment"], "movement": ["motion_smoothness"], "consistency": ["posture_consistency"], "stability": ["trunk_stability", "head_control"]}},
}

DEFAULT_COMPONENT_WEIGHTS = {"technique": 0.20, "balance": 0.20, "movement": 0.20, "consistency": 0.20, "stability": 0.20}


def _normalized_weights(weights: dict):
    total = sum(weights.values())
    return {key: value / total for key, value in weights.items()} if total else dict(DEFAULT_COMPONENT_WEIGHTS)


def _build_missing_profiles():
    movement_terms = ("footwork", "dribbling", "running", "defend", "fielding", "hurdle", "jump", "digging", "blocking")
    technique_terms = ("serve", "batting", "bowling", "passing", "forehand", "backhand", "shoot", "setting", "throw", "spik", "smash")
    for sport, config in SPORT_ANALYSIS_CONFIG.items():
        base = _normalized_weights({key: config["scoring_weights"][key] for key in DEFAULT_COMPONENT_WEIGHTS})
        activity_profiles = config.setdefault("activity_weights", {})
        for activity in config["activities"]:
            if activity in activity_profiles:
                continue
            weights = dict(base)
            normalized_activity = activity.casefold()
            if any(term in normalized_activity for term in movement_terms):
                weights["movement"] *= 1.5
                weights["balance"] *= 1.15
            elif any(term in normalized_activity for term in technique_terms):
                weights["technique"] *= 1.35
                weights["stability"] *= 1.15
            elif sport == "Swimming":
                weights["technique"] *= 1.2
                weights["consistency"] *= 1.2
            activity_profiles[activity] = _normalized_weights(weights)

        role_profiles = config.setdefault("role_weights", {})
        for role in config["roles"]:
            if role in role_profiles:
                continue
            weights = dict(base)
            normalized_role = role.casefold()
            if any(term in normalized_role for term in ("keeper", "center", "libero", "blocker", "back")):
                weights["balance"] *= 1.25
                weights["stability"] *= 1.25
            elif any(term in normalized_role for term in ("forward", "winger", "sprinter", "hurdler", "point guard", "midfielder")):
                weights["movement"] *= 1.25
            else:
                weights["technique"] *= 1.15
            role_profiles[role] = _normalized_weights(weights)

        focus = config.get("metric_focus", {})
        config["performance_metrics"] = focus
        for category in ("technique", "balance", "movement", "consistency", "stability"):
            config[f"{category}_metrics"] = focus.get(category, [])
        config["role_specific_metrics"] = {
            role: [metric for category, _ in sorted(role_profiles[role].items(), key=lambda item: item[1], reverse=True)[:3] for metric in focus.get(category, [])]
            for role in config["roles"]
        }
        config["activity_specific_metrics"] = {
            activity: [metric for category, _ in sorted(activity_profiles[activity].items(), key=lambda item: item[1], reverse=True)[:3] for metric in focus.get(category, [])]
            for activity in config["activities"]
        }
        config["coaching_rules"] = {"strength_threshold": 80, "weakness_threshold": 60, "repeated_session_minimum": 2}


_build_missing_profiles()


def get_sport_config(sport: str):
    normalized = (sport or "").strip().casefold()
    return next((config for name, config in SPORT_ANALYSIS_CONFIG.items() if name.casefold() == normalized), None)


def get_named_weights(config: dict, category: str, name: str):
    profiles = config.get(f"{category}_weights", {})
    normalized = (name or "").strip().casefold()
    return next((weights for profile_name, weights in profiles.items() if profile_name.casefold() == normalized), None)