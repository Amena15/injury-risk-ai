# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Injury Risk AI"
    VERSION: str = "1.0.0"
    MAX_VIDEO_DURATION: int = 15  # seconds
    MIN_CONFIDENCE: float = 0.5   # MediaPipe detection threshold
    RISK_THRESHOLDS = {
        "LOW": 0,
        "MODERATE": 40,
        "HIGH": 70
    }

settings = Settings()