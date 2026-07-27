import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Any

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

class PoseAnalyzer:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.pose = mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.resize_dim = (320, 240)  # smaller = much faster processing

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        # Resize frame to 320x240 for ~80% faster processing
        frame = cv2.resize(frame, self.resize_dim, interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        if not results.pose_landmarks:
            return None

        landmarks = results.pose_landmarks.landmark

        def get_coords(idx):
            return [landmarks[idx].x, landmarks[idx].y, landmarks[idx].z]

        def angle_between_points(a, b, c):
            a, b, c = np.array(a), np.array(b), np.array(c)
            ba = a - b
            bc = c - b
            cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
            angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
            return angle

        left_shoulder = get_coords(11)
        right_shoulder = get_coords(12)
        left_elbow = get_coords(13)
        right_elbow = get_coords(14)
        left_wrist = get_coords(15)
        right_wrist = get_coords(16)
        left_hip = get_coords(23)
        right_hip = get_coords(24)
        left_knee = get_coords(25)
        right_knee = get_coords(26)
        left_ankle = get_coords(27)
        right_ankle = get_coords(28)

        metrics = {
            'left_elbow_angle': angle_between_points(left_shoulder, left_elbow, left_wrist),
            'right_elbow_angle': angle_between_points(right_shoulder, right_elbow, right_wrist),
            'left_knee_angle': angle_between_points(left_hip, left_knee, left_ankle),
            'right_knee_angle': angle_between_points(right_hip, right_knee, right_ankle),
            'left_shoulder_angle': angle_between_points(left_elbow, left_shoulder, left_hip),
            'right_shoulder_angle': angle_between_points(right_elbow, right_shoulder, right_hip),
            'hip_angle': angle_between_points(
                get_coords(11),
                [(left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2, (left_hip[2] + right_hip[2]) / 2],
                get_coords(25)
            ),
        }
        return metrics

    def process_video(self, video_path: str) -> List[Dict[str, Any]]:
        cap = cv2.VideoCapture(video_path)
        all_metrics = []
        frame_count = 0
        processed_frames = 0
        max_frames = 50  # limit to 50 frames total (~1.5s of movement)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            # Process only every 5th frame
            if frame_count % 5 != 0:
                continue
            metrics = self.process_frame(frame)
            if metrics:
                all_metrics.append(metrics)
                processed_frames += 1
            if processed_frames >= max_frames:
                break

        cap.release()
        return all_metrics
