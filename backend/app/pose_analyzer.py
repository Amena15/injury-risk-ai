import cv2
import mediapipe as mp
import numpy as np
import os
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional

class PoseAnalyzer:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.pose = None
        self.landmarker = None
        self._tasks_mode = not hasattr(mp, "solutions")
        self._last_timestamp_ms = -1
        self.resize_dim = (320, 240)  # smaller = much faster processing

        if self._tasks_mode:
            model_path = self._get_task_model_path()
            options = mp.tasks.vision.PoseLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                min_pose_detection_confidence=min_detection_confidence,
                min_pose_presence_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                num_poses=1,
            )
            self.landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        else:
            self.pose = mp.solutions.pose.Pose(
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )

    @staticmethod
    def _get_task_model_path() -> Path:
        configured_path = os.getenv("MEDIAPIPE_POSE_MODEL")
        if configured_path:
            model_path = Path(configured_path).expanduser()
            if not model_path.is_file():
                raise FileNotFoundError(f"MediaPipe pose model not found: {model_path}")
            return model_path

        model_path = Path.home() / ".cache" / "injury-risk-ai" / "pose_landmarker_lite.task"
        if not model_path.is_file():
            model_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = model_path.with_suffix(".task.download")
            model_url = (
                "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
                "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
            )
            try:
                urllib.request.urlretrieve(model_url, temporary_path)
                temporary_path.replace(model_path)
            finally:
                if temporary_path.exists():
                    temporary_path.unlink()
        return model_path

    def process_frame(self, frame: np.ndarray, timestamp_ms: Optional[int] = None) -> Dict[str, Any]:
        # Resize frame to 320x240 for ~80% faster processing
        frame = cv2.resize(frame, self.resize_dim, interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self._tasks_mode:
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            requested_timestamp = 0 if timestamp_ms is None else timestamp_ms
            timestamp_ms = max(requested_timestamp, self._last_timestamp_ms + 1)
            self._last_timestamp_ms = timestamp_ms
            results = self.landmarker.detect_for_video(image, timestamp_ms)
            pose_landmarks = results.pose_landmarks[0] if results.pose_landmarks else None
        else:
            results = self.pose.process(rgb)
            pose_landmarks = results.pose_landmarks.landmark if results.pose_landmarks else None

        if not pose_landmarks:
            return None

        landmarks = pose_landmarks

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
        if not cap.isOpened():
            cap.release()
            return all_metrics

        frame_count = 0
        processed_frames = 0
        max_frames = 50  # limit to 50 frames total (~1.5s of movement)
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if np.isfinite(fps) and fps > 0 else 30.0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
                if frame_count % 5 != 0:
                    continue
                timestamp_ms = int(frame_count * 1000 / fps)
                metrics = self.process_frame(frame, timestamp_ms=timestamp_ms)
                if metrics:
                    all_metrics.append(metrics)
                    processed_frames += 1
                if processed_frames >= max_frames:
                    break
        finally:
            cap.release()
        return all_metrics

    def close(self):
        if self.landmarker is not None:
            self.landmarker.close()
        if self.pose is not None:
            self.pose.close()
