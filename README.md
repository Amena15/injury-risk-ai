# Injury Risk AI

AI‑powered tennis injury prevention with a FastAPI backend, a React Native mobile app, and an **asynchronous Celery + Redis task pipeline** for real‑time video processing.

## Overview

Injury Risk AI records or uploads a short tennis stroke video, extracts pose landmarks, computes joint angles, and returns a risk level with corrective guidance. The app supports both a trained ML model and a rule‑based fallback engine.

Processing is fully asynchronous: the frontend submits a job and polls for results – no timeouts, no stuck progress bars.

## Screenshots

<p align="center">
  <img src="assets/mainDashboard.png" alt="Main Dashboard" width="220"/>
</p>

<p align="center">
  <img src="assets/analysis3.png" alt="Analysis Screen 3" width="220"/>
  <img src="assets/analysis1.png" alt="Analysis Screen 1" width="220"/>
  <img src="assets/analysis2.png" alt="Analysis Screen 2" width="220"/>
</p>

<p align="center">
  <img src="assets/Dataset%20Analysis%20Summary.png" alt="Dataset Analysis Summary" width="750"/>
</p>

## Key Features

- Video capture and upload from the mobile app
- MediaPipe‑based pose estimation and joint‑angle extraction
- ML risk prediction (RandomForest) with rule‑based fallback
- **Asynchronous background processing** with Celery + Redis – no timeouts
- Risk score, flagged joint, risk factors, and recommendations
- Temporary processing – uploaded videos are deleted after analysis

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| Frontend | React Native + Expo |
| Backend API | FastAPI (Python) |
| Task Queue | Celery + Redis |
| Pose Estimation | MediaPipe |
| ML Model | scikit‑learn RandomForest |
| Deployment | (local / cloud ready) |

## Project Structure

```
injury-risk-ai/
├── backend/
│   ├── app/                # FastAPI app
│   ├── celery_app.py       # Celery configuration
│   ├── tasks.py            # Celery tasks (video processing)
│   ├── models/             # Trained ML pipelines
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── .env
│   └── package.json
├── Dataset/                # Local training assets (ignored by Git)
└── assets/                 # Screenshots for README
```

## Backend Setup

Use Python 3.11 or newer and Node.js 22 (Expo warns on Node 20.17.0). Prepare the backend environment once from the project root:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

Make sure **Redis** is installed (macOS):

```bash
brew install redis
```

## Frontend Setup

```bash
cd frontend
npm install
```

## Run The App

Expo uses the async API, so each run needs Redis, a Celery worker, the API, and Expo running. Open four terminals from the project root.

Terminal 1, start Redis:

```bash
brew services start redis
```

Terminal 2, start the Celery worker:

```bash
cd backend
source venv/bin/activate
MEDIAPIPE_DISABLE_GPU=1 PYTHONPATH=. celery -A celery_app worker --loglevel=info --concurrency=1 --pool=solo
```

The `--pool=solo` and `MEDIAPIPE_DISABLE_GPU=1` avoid MediaPipe fork-related crashes on macOS.

Terminal 3, start FastAPI:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Wait for the API to start, then check `http://127.0.0.1:8000/health`.

Terminal 4, start Expo using Node.js 22:

```bash
cd frontend
nvm use 22
EXPO_PUBLIC_API_URL="http://$(ipconfig getifaddr en0):8000" npm run start -- --lan --clear
```

Open `http://localhost:8081/` on the Mac. If Expo reports that port 8081 is occupied and offers another port, use the URL it prints instead.

For a physical phone on the same Wi-Fi, scan the QR code shown by Expo. The API URL above uses the Mac's current Wi-Fi address; if your active network interface is not `en0`, replace the value with the Mac's LAN IP. Keep Redis, the worker, API, and Expo running while using the app.

To stop the app, press `Ctrl+C` in the worker, API, and Expo terminals. Run the same commands next time; Redis can stay managed by `brew services`.

On first startup, MediaPipe Tasks downloads the lightweight pose model to `~/.cache/injury-risk-ai/`. Set `MEDIAPIPE_POSE_MODEL` to a local `.task` file to use a pre-provisioned model or run offline. Uploaded videos are analyzed from sampled frames; the API returns an error if no pose is detected. The leak-free ML pipeline is preferred when `backend/models/leak_free_risk_pipeline.pkl` exists; otherwise the API tries the earlier enhanced and legacy models before using the rule-based fallback.

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/analyze` | Multipart video upload (sync, fallback) |
| `POST` | `/analyze-json` | Base64 video upload (sync) |
| `POST` | `/analyze-async` | **Submit a video for async processing** – returns `job_id` |
| `GET` | `/job-status/{job_id}` | Poll for job status and result |
| `POST` | `/analyze/compare` | Compare ML vs rule‑based outputs (debug) |
| `GET` | `/health` | Health check and ML availability |

## How It Works (Async Flow)

1. **Mobile app** records or picks a video → encodes as Base64.
2. **`POST /analyze-async`** → FastAPI creates a Celery task and returns a `job_id` **instantly**.
3. **Celery worker** processes the video (pose estimation → angles → risk prediction).
4. **App polls** `GET /job-status/{job_id}` every 2 seconds until the result is ready.
5. **Result appears** – no timeouts, no “stuck at 98%”.

## Model Notes

- The backend loads `backend/models/leak_free_risk_pipeline.pkl` first when available.
- If the model artifact is incompatible with installed packages, the API falls back to the rule-based engine instead of crashing.
- To regenerate the legacy model with current dependencies:

```bash
cd backend
source venv/bin/activate
python train_model.py
```

## Enhanced Model And Active Learning

From the project root, activate the backend environment and run the leak-free training script to regenerate the pipeline and paper plots:

```bash
source backend/venv/bin/activate
cd backend
python training/final_leak_free_train.py
python training/active_learning_selector.py
```

Training writes `backend/models/leak_free_risk_pipeline.pkl` and the plots `assets/confusion_matrix.png` and `assets/feature_importance.png`. The selector writes 50 uncertain samples to `backend/data_processing/for_expert_labeling.csv`. The file omits the existing heuristic risk labels and includes a blank `expert_risk_level` column for independent review. Review and merge expert labels into the training data before retraining.

The current leak-free holdout accuracy is 94.2% on a 52-sample test split. Labels are risk categories generated by this project's rule engine, not observed injuries or independent clinical labels; this result must not be presented as clinical injury-prediction accuracy. The local API smoke test used an MP4 assembled from repository tennis images because no camera-recorded video is included in the workspace. Test a short Expo-recorded clip on the target device before treating device capture as verified.

## Troubleshooting

- `fetch failed: Could not connect to the server`
  - Make sure the backend is running with `--host 0.0.0.0`
  - Make sure the phone and Mac are on the same Wi-Fi
  - Restart Expo with `EXPO_PUBLIC_API_URL` set to the Mac's current LAN IP as shown above
- Expo warns about the Node version
  - Run `nvm use 22` in the frontend terminal before starting Expo
- Port 8081 is already in use
  - Stop the other Expo process or use the alternate port Expo offers and open its printed URL
- Model load error on backend startup
  - Rebuild the model with `python train_model.py`
- Celery worker cannot connect to Redis
  - Run `brew services start redis` and check `redis-cli ping` returns `PONG`
- Celery worker crashes with `SIGABRT`
  - Start it with `MEDIAPIPE_DISABLE_GPU=1` and `--pool=solo`
