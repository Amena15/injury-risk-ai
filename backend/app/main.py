# backend/app/main.py
import os
import tempfile
import shutil
import subprocess
import base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult
from app.config import settings
from app.pose_analyzer import PoseAnalyzer
from app.risk_engine import RiskEngine
from app.ml_risk_engine import MLRiskEngine
from tasks import process_video_task
import numpy as np

from celery.result import AsyncResult



# --- JSON payload model for base64 upload ---
class VideoPayload(BaseModel):
    file: str   # base64 encoded video data
    filename: str
    type: str

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = PoseAnalyzer(
    min_detection_confidence=settings.MIN_CONFIDENCE,
    min_tracking_confidence=settings.MIN_CONFIDENCE
)

MAX_VIDEO_SIZE_MB = 20

@app.on_event("startup")
def startup_event():
    loaded = MLRiskEngine.load_model()
    if loaded:
        print("✅ ML Risk Engine is active.")
    else:
        print("⚠️ ML model not found — falling back to rule-based RiskEngine.")

def compress_video(input_path: str, max_size_mb: int = MAX_VIDEO_SIZE_MB) -> str:
    original_size = os.path.getsize(input_path) / (1024 * 1024)
    if original_size <= max_size_mb:
        return input_path

    output_path = input_path.replace(".", "_compressed.")
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-vcodec", "libx264", "-crf", "28",
             "-preset", "fast", "-acodec", "aac", "-b:a", "64k",
             "-y", output_path],
            capture_output=True,
            timeout=60,
            check=True,
        )
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)
        if compressed_size > max_size_mb:
            # More aggressive compression
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", input_path],
                capture_output=True, text=True, timeout=15,
            )
            duration = float(probe.stdout.strip() or 10)
            target_bitrate = int((max_size_mb * 8 * 0.9 * 1024) / duration)
            target_bitrate = max(target_bitrate, 100)

            subprocess.run(
                ["ffmpeg", "-i", input_path, "-vcodec", "libx264",
                 "-b:v", f"{target_bitrate}k", "-preset", "fast",
                 "-acodec", "aac", "-b:a", "48k",
                 "-y", output_path],
                capture_output=True,
                timeout=60,
                check=True,
            )
        return output_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        if os.path.exists(output_path):
            os.unlink(output_path)
        return input_path

def process_video_file(video_path: str):
    """Common video processing logic used by both endpoints."""
    all_metrics = analyzer.process_video(video_path)
    if not all_metrics:
        raise HTTPException(400, "No pose detected in the video. Ensure you are visible and moving.")

    avg_metrics = {}
    for key in all_metrics[0].keys():
        avg_metrics[key] = float(np.mean([m[key] for m in all_metrics]))

    use_ml = MLRiskEngine.is_available()
    if use_ml:
        risk = MLRiskEngine.predict_risk(avg_metrics)
        overall_risk_level = risk['risk_level']
        max_risk_score = risk['risk_score']
        primary_risk_factors = risk['primary_risk_factors']
        recommendations = risk['recommendations']
        flagged_joint = risk['flagged_joint']
        flagged_label = risk['flagged_label']
    else:
        frame_risks = []
        for frame_metrics in all_metrics:
            risk = RiskEngine.evaluate_metrics(frame_metrics)
            frame_risks.append(risk)
        worst_frame = max(frame_risks, key=lambda x: x["risk_score"])
        overall_risk_level = worst_frame["risk_level"]
        max_risk_score = worst_frame["risk_score"]
        flagged_joint = worst_frame.get("flagged_joint", "right_elbow")
        flagged_label = worst_frame.get("flagged_label", "Right elbow")
        primary_risk_factors = worst_frame["risk_factors"]
        recommendations = RiskEngine.generate_recommendations(worst_frame["risk_factors"])

    return {
        "average_metrics": avg_metrics,
        "risk_engine": "ml" if use_ml else "rule",
        "overall_risk_level": overall_risk_level,
        "max_risk_score": max_risk_score,
        "flagged_joint": flagged_joint,
        "flagged_label": flagged_label,
        "primary_risk_factors": primary_risk_factors,
        "recommendations": recommendations,
    }

# --- Existing /analyze endpoint (multipart) ---
@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video.")

    try:
        suffix = os.path.splitext(file.filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(500, f"Failed to save video: {str(e)}")

    compressed_path = None
    try:
        compressed_path = compress_video(tmp_path)
        video_to_process = compressed_path if compressed_path != tmp_path else tmp_path
        result = process_video_file(video_to_process)
        if compressed_path and compressed_path != tmp_path:
            try:
                os.unlink(compressed_path)
            except OSError:
                pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return result

# --- Existing /analyze-json endpoint (synchronous base64) ---
@app.post("/analyze-json")
async def analyze_video_json(payload: VideoPayload):
    tmp_path = None
    try:
        video_bytes = base64.b64decode(payload.file)
        if len(video_bytes) == 0:
            raise HTTPException(400, "Empty video file.")
        suffix = os.path.splitext(payload.filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        result = process_video_file(tmp_path)
        return result
    except HTTPException:
        raise
    except base64.binascii.Error as e:
        raise HTTPException(400, f"Invalid base64 encoding: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

# # --- NEW: Async endpoints for background processing ---
# @app.post("/analyze-async")
# async def start_analysis(payload: VideoPayload):
#     """Submit a video for asynchronous processing."""
#     task = process_video_task.delay(payload.file, payload.filename)
#     return {
#         "job_id": task.id,
#         "status": "queued",
#         "message": "Video submitted. Poll /job-status/{job_id} for results."
#     }

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of an async job."""
    task = AsyncResult(job_id, app=process_video_task)
    if task.state == 'PENDING':
        return {"status": "pending", "progress": 0}
    elif task.state == 'STARTED':
        return {"status": "processing", "progress": 50}
    elif task.state == 'FAILURE':
        return {"status": "failed", "error": str(task.info)}
    elif task.state == 'SUCCESS':
        return {"status": "success", "result": task.result}
    else:
        return {"status": task.state}

# --- /analyze/compare (existing) ---
@app.post("/analyze/compare")
async def analyze_compare(file: UploadFile = File(...)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(400, "File must be a video.")

    try:
        suffix = os.path.splitext(file.filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(500, f"Failed to save video: {str(e)}")

    try:
        all_metrics = analyzer.process_video(tmp_path)
        if not all_metrics:
            raise HTTPException(400, "No pose detected in the video.")
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    avg_metrics = {}
    for key in all_metrics[0].keys():
        avg_metrics[key] = float(np.mean([m[key] for m in all_metrics]))

    ml_result = None
    if MLRiskEngine.is_available():
        ml_risk = MLRiskEngine.predict_risk(avg_metrics)
        ml_result = {
            "risk_level": ml_risk['risk_level'],
            "risk_score": ml_risk['risk_score'],
            "probabilities": ml_risk.get('probabilities'),
            "primary_risk_factors": ml_risk['primary_risk_factors'],
            "recommendations": ml_risk['recommendations'],
        }

    frame_risks = []
    for frame_metrics in all_metrics:
        frame_risks.append(RiskEngine.evaluate_metrics(frame_metrics))
    worst_frame = max(frame_risks, key=lambda x: x["risk_score"])

    rule_result = {
        "risk_level": worst_frame["risk_level"],
        "risk_score": worst_frame["risk_score"],
        "flagged_joint": worst_frame.get("flagged_joint", "right_elbow"),
        "flagged_label": worst_frame.get("flagged_label", "Right elbow"),
        "primary_risk_factors": worst_frame["risk_factors"],
        "recommendations": RiskEngine.generate_recommendations(worst_frame["risk_factors"]),
    }

    return {
        "average_metrics": avg_metrics,
        "ml": ml_result,
        "rule_based": rule_result,
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "ml_engine_available": MLRiskEngine.is_available(),
    }


@app.post("/analyze-async")
async def start_analysis(payload: VideoPayload):
    """Submit a video for asynchronous processing."""
    task = process_video_task.delay(payload.file, payload.filename)
    return {
        "job_id": task.id,
        "status": "queued",
        "message": "Video submitted. Poll /job-status/{job_id} for results."
    }

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of an async job."""
    task = AsyncResult(job_id, app=process_video_task)
    if task.state == 'PENDING':
        return {"status": "pending", "progress": 0}
    elif task.state == 'STARTED':
        return {"status": "processing", "progress": 50}
    elif task.state == 'FAILURE':
        return {"status": "failed", "error": str(task.info)}
    elif task.state == 'SUCCESS':
        return {"status": "success", "result": task.result}
    else:
        return {"status": task.state}