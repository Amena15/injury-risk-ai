# 🏸 Injury Risk AI

> AI-powered tennis injury prevention – analyze movement, predict risk, stay on court.

⚡ **Machine Learning** | 🎯 **Computer Vision** | 📱 **React Native** | 🐍 **FastAPI** | 🧠 **MediaPipe** | 🏷️ **TensorFlow Lite ready** | 🔄 **Real-time**

---

## 📖 Overview

**Injury Risk AI** is a mobile-first wellness platform for tennis players. Using your smartphone’s camera, it records a short video of your serve or stroke, runs real-time pose estimation to extract joint angles, and predicts your injury risk level (Low / Moderate / High) using a trained machine learning model.

The app then gives you **personalized corrective exercises** and highlights the **specific biomechanical issues** that may lead to common tennis injuries like tennis elbow, shoulder impingement, or knee stress.

## ✨ Key Features

*   **🎥 Video Capture:** Record 5–13 seconds of a tennis stroke using the built-in camera, or upload from your gallery.
*   **🧍 Pose Estimation:** MediaPipe extracts 33 body landmarks, computing left/right elbow, knee, shoulder, and hip angles.
*   **🤖 ML Risk Prediction:** Random Forest classifier (96% accuracy) trained on 260 annotated frames – predicts risk level instantly.
*   **📊 Actionable Feedback:** Get detailed risk factors, a risk score (0–100), and tailored “prehab” exercises to correct your form.
*   **📈 Progress Tracking:** Monitor your risk trend over time (future feature – ready for extension).
*   **🔒 Privacy-First:** Videos are processed on-the-fly and never stored – all analysis is temporary and local.

## 🛠️ Tech Stack

*   **Frontend:** React Native (Expo) – cross-platform mobile app with a clean, dark theme.
*   **Backend:** FastAPI (Python) – RESTful API serving the ML model and pose analysis.
*   **Pose Estimation:** MediaPipe (0.10.8) – classic `mp.solutions.pose` for fast landmark detection.
*   **ML Model:** Scikit-learn RandomForest – trained on joint-angle features from the Tennis Player Actions dataset.
*   **Video Upload:** Base64 encoding (JSON) – bypasses iOS `FormData` issues, ensures reliability.
*   **Deployment:** Docker-ready (backend) + Expo EAS (mobile builds).

## 📦 Installation & Setup

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
The server runs at http://localhost:8000. The ML model loads automatically on startup.
Frontend (React Native / Expo)
Bash
cd frontend
npm install
npx expo start
Scan the QR code with Expo Go on your phone, or press i for iOS simulator / a for Android emulator.
Environment Variables
Create a .env file in the backend root (optional):
Code snippet
# backend/.env
MIN_CONFIDENCE=0.5
MAX_VIDEO_SIZE_MB=20
🔌 API Endpoints
POST /analyze-json – Upload a base64-encoded video (JSON) → returns risk analysis.
POST /analyze – Multipart video upload (alternative, but not recommended for iOS).
GET /health – Health check; reports if ML engine is available.
POST /analyze/compare – Compare ML vs rule-based outputs (debugging).
Example JSON payload:
JSON
{
  "file": "base64_encoded_video_string",
  "filename": "serve.mp4",
  "type": "video/mp4"
}
📊 Dataset & Training
The ML model was trained on the Tennis Player Actions Dataset (Kaggle), which contains 2,000 images of forehand, backhand, serve, and ready positions. We extracted 7 joint angles per image and labelled them with our rule-based risk engine, then trained a RandomForest classifier achieving ~96% test accuracy.
To extend the model, you can use the THETIS dataset (8,374 video sequences) with 3D skeleton data – ideal for more advanced time-series models (LSTM / Transformers).
🤝 Contributing
We welcome contributions! Please follow standard GitHub flow:
Fork the repository
Create a feature branch
Commit your changes
Open a pull request
For major changes, please open an issue first to discuss what you would like to change.
📄 License
This project is licensed under the MIT License – see the LICENSE file for details.
🙏 Acknowledgements
MediaPipe – for seamless pose estimation.
FastAPI – for the lightning-fast Python API.
Scikit-learn – for the RandomForest classifier.
Expo – for making React Native development a breeze.
Tennis Player Actions Dataset – for providing the annotated images.
