# Injury Risk AI

AI-powered tennis injury prevention with a FastAPI backend and an Expo mobile app.

## Overview

Injury Risk AI records or uploads a short tennis stroke video, extracts pose landmarks, computes joint angles, and returns a risk level with suggested corrective guidance. The app supports both a trained ML model and a rule-based fallback engine.

## Screenshots

<p align="center">
  <img src="assets/mainDashboard.png" alt="Main Dashboard" width="220"/>
  <img src="assets/analysis1.png" alt="Analysis Screen 1" width="220"/>
</p>

<p align="center">
  <img src="assets/analysis2.png" alt="Analysis Screen 2" width="220"/>
  <img src="assets/analysis3.png" alt="Analysis Screen 3" width="220"/>
</p>

<p align="center">
  <img src="assets/Dataset%20Analysis%20Summary.png" alt="Dataset Analysis Summary" width="750"/>
</p>

## Key Features

- Video capture and upload from the mobile app
- MediaPipe-based pose estimation and joint-angle extraction
- ML risk prediction with rule-based fallback
- Risk score, flagged joint, risk factors, and recommendations
- Temporary processing flow without storing uploaded videos

## Tech Stack

- Frontend: React Native with Expo
- Backend: FastAPI
- Pose estimation: MediaPipe
- ML model: scikit-learn RandomForest

## Project Structure

- `backend/` FastAPI API, pose analysis, rule-based and ML risk engines
- `frontend/` Expo/React Native mobile app
- `Dataset/` local training dataset assets

## Backend Setup

```bash
cd backend
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env` with your Mac LAN IP:

```env
EXPO_PUBLIC_API_URL=http://192.168.100.225:8000
```

If your Wi-Fi changes, update the IP before starting Expo again.

## Run The Working Version

Start the backend first:

```bash
cd backend
source ./venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Check health:

- Mac: `http://127.0.0.1:8000/health`
- Phone on same Wi-Fi: `http://192.168.100.225:8000/health`

Start the frontend:

```bash
npm --prefix /Users/amena/Desktop/injury-risk-ai/frontend run start -- --lan -c
```

If Expo asks to switch from port `8081` to `8082`, accept it.

## API Endpoints

- `POST /analyze-json` base64 video upload via JSON
- `POST /analyze` multipart video upload
- `POST /analyze/compare` compare ML vs rule-based output
- `GET /health` health check and ML availability

## Model Notes

- The backend loads `backend/risk_model.pkl` when available.
- If the model artifact is incompatible with installed packages, the API falls back to the rule-based engine instead of crashing.
- To regenerate the model with current dependencies:

```bash
cd backend
source ./venv/bin/activate
python train_model.py
```

## Troubleshooting

- `fetch failed: Could not connect to the server`
  - Make sure the backend is running with `--host 0.0.0.0`
  - Make sure the phone and Mac are on the same Wi-Fi
  - Confirm `frontend/.env` points to the current Mac LAN IP
- Expo starts from the wrong folder
  - Use `npm --prefix /Users/amena/Desktop/injury-risk-ai/frontend run start -- --lan -c`
- Model load error on backend startup
  - Rebuild the model with `python train_model.py`
