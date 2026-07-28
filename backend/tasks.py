# backend/tasks.py
import base64
import tempfile
import os
import numpy as np
from celery_app import celery
from app.pose_analyzer import PoseAnalyzer
from app.ml_risk_engine import MLRiskEngine
from app.risk_engine import RiskEngine


@celery.task(bind=True)
def process_video_task(self, base64_data, filename):
    """Background task to process a video and return risk analysis."""
    try:
        # 1. Decode and save video
        video_bytes = base64.b64decode(base64_data)
        suffix = os.path.splitext(filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        # 2. Process video (same logic as before)
        analyzer = PoseAnalyzer()
        all_metrics = analyzer.process_video(tmp_path)
        if not all_metrics:
            os.unlink(tmp_path)
            raise ValueError("No pose detected in the video.")

        avg_metrics = {}
        for key in all_metrics[0].keys():
            avg_metrics[key] = float(np.mean([m[key] for m in all_metrics]))

        # 3. Use ML or rule-based
        use_ml = MLRiskEngine.is_available()
        if use_ml:
            risk = MLRiskEngine.predict_risk(avg_metrics)
            result = {
                "overall_risk_level": risk['risk_level'],
                "max_risk_score": risk['risk_score'],
                "primary_risk_factors": risk['primary_risk_factors'],
                "recommendations": risk['recommendations'],
                "flagged_joint": risk.get('flagged_joint'),
                "flagged_label": risk.get('flagged_label'),
                "average_metrics": avg_metrics,
            }
        else:
            frame_risks = []
            for frame_metrics in all_metrics:
                frame_risks.append(RiskEngine.evaluate_metrics(frame_metrics))
            worst_frame = max(frame_risks, key=lambda x: x["risk_score"])
            result = {
                "overall_risk_level": worst_frame["risk_level"],
                "max_risk_score": worst_frame["risk_score"],
                "primary_risk_factors": worst_frame["risk_factors"],
                "recommendations": RiskEngine.generate_recommendations(worst_frame["risk_factors"]),
                "flagged_joint": worst_frame.get("flagged_joint", "right_elbow"),
                "flagged_label": worst_frame.get("flagged_label", "Right elbow"),
                "average_metrics": avg_metrics,
            }

        # 4. Clean up
        os.unlink(tmp_path)
        return result

    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise