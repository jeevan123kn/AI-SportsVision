import math


def compute_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def get_landmark_points(landmarks, indices):
    points = []
    for idx in indices:
        if idx < len(landmarks):
            points.append((landmarks[idx]["x"], landmarks[idx]["y"]))
    return points


def calculate_joint_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0]*bc[0] + ba[1]*bc[1]
    norm = math.hypot(*ba) * math.hypot(*bc)
    if norm == 0:
        return 0.0
    cos_theta = max(-1.0, min(1.0, dot / norm))
    return math.degrees(math.acos(cos_theta))


def extract_features(landmarks):
    if not landmarks or len(landmarks) < 33:
        return {
            "status": "Insufficient pose data",
            "metrics": {},
        }

    left_shoulder = get_landmark_points(landmarks, [11])[0]
    right_shoulder = get_landmark_points(landmarks, [12])[0]
    left_elbow = get_landmark_points(landmarks, [13])[0]
    right_elbow = get_landmark_points(landmarks, [14])[0]
    left_wrist = get_landmark_points(landmarks, [15])[0]
    right_wrist = get_landmark_points(landmarks, [16])[0]
    left_hip = get_landmark_points(landmarks, [23])[0]
    right_hip = get_landmark_points(landmarks, [24])[0]
    left_knee = get_landmark_points(landmarks, [25])[0]
    right_knee = get_landmark_points(landmarks, [26])[0]
    left_ankle = get_landmark_points(landmarks, [27])[0]
    right_ankle = get_landmark_points(landmarks, [28])[0]
    nose = get_landmark_points(landmarks, [0])[0]

    left_elbow_angle = calculate_joint_angle(left_shoulder, left_elbow, left_wrist)
    right_elbow_angle = calculate_joint_angle(right_shoulder, right_elbow, right_wrist)
    left_knee_angle = calculate_joint_angle(left_hip, left_knee, left_ankle)
    right_knee_angle = calculate_joint_angle(right_hip, right_knee, right_ankle)
    shoulder_alignment = abs(left_shoulder[1] - right_shoulder[1])
    head_stability = 1.0 - min(1.0, abs(nose[1] - ((left_shoulder[1] + right_shoulder[1]) / 2.0)))

    return {
        "status": "Pose data available",
        "metrics": {
            "left_elbow_angle": round(left_elbow_angle, 2),
            "right_elbow_angle": round(right_elbow_angle, 2),
            "left_knee_angle": round(left_knee_angle, 2),
            "right_knee_angle": round(right_knee_angle, 2),
            "shoulder_alignment": round(shoulder_alignment, 4),
            "head_stability": round(head_stability, 4),
            "left_hip_y": round(left_hip[1], 4),
            "right_hip_y": round(right_hip[1], 4),
            "foot_movement": round(compute_distance(left_ankle, right_ankle), 4),
        },
    }
