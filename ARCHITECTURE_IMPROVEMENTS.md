# Architecture Improvement Plan - Injury Risk AI

## Executive Summary

This document outlines a comprehensive architecture improvement strategy for the Injury Risk AI application, focusing on performance optimization, accuracy enhancement, and infrastructure scalability. The current architecture has several bottlenecks that limit both performance and accuracy potential.

## Current Architecture Analysis

### Critical Bottlenecks Identified

1. **Video Upload Performance**
   - Base64 encoding increases video size by 33%
   - No proper timeout handling or streaming
   - Single-threaded processing blocks API responses
   - Current timeout at 98% progress indicates poor user experience

2. **Pose Estimation Performance**
   - 320x240 resolution for speed but sacrifices accuracy
   - Processes only every 5th frame (20% sampling)
   - Limited to 50 frames total (~1.5s of movement)
   - No frame quality filtering or confidence scoring

3. **ML Model Limitations**
   - Small dataset (~280 samples) limits model generalization
   - Single RandomForest model with fixed hyperparameters
   - No model versioning or A/B testing capabilities
   - Missing feature engineering (temporal dynamics, velocity, acceleration)

4. **Infrastructure Issues**
   - No horizontal scaling capability
   - Celery configured but not actively used
   - No caching layer for repeated analyses
   - No monitoring or observability
   - Single-server architecture creates single point of failure

5. **Data Pipeline Problems**
   - Dataset processing creates static CSV
   - No continuous training pipeline
   - Missing data validation and quality checks
   - No user feedback loop for model improvement

## Performance Optimization Strategy

### 1. Video Upload Enhancement (High Priority)

**Current Issues:**
- Base64 encoding overhead (33% size increase)
- No streaming or chunked uploads
- Poor timeout handling

**Solutions:**
```python
# Implement multipart streaming upload
@app.post("/analyze")
async def analyze_video_streaming(file: UploadFile = File(...)):
    # Stream upload directly to disk without base64
    async with aiofiles.open(temp_path, 'wb') as f:
        async for chunk in file.file.iter_chunked(1024 * 1024):  # 1MB chunks
            await f.write(chunk)
    
    # Immediate response with job ID
    job_id = str(uuid.uuid4())
    process_video_task.delay(job_id, temp_path)
    return {"job_id": job_id, "status": "processing"}
```

**Benefits:**
- 33% reduction in upload size
- True streaming capability
- Better memory efficiency
- Immediate user feedback

### 2. Pose Estimation Optimization

**Current Issues:**
- Fixed low resolution (320x240)
- Aggressive frame sampling (20%)
- No quality-based frame selection

**Solutions:**
```python
class OptimizedPoseAnalyzer:
    def __init__(self):
        # Adaptive resolution based on device capabilities
        self.high_quality_pose = mp_pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=2  # Higher accuracy model
        )
        self.fast_pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0  # Faster model
        )
    
    def process_video_adaptive(self, video_path):
        # Start with fast pass for quality assessment
        quality_score = self.assess_video_quality(video_path)
        
        # Select processing strategy based on quality
        if quality_score > 0.8:
            return self.process_high_quality(video_path)
        else:
            return self.process_fast(video_path)
```

**Benefits:**
- Adaptive quality based on input
- Better accuracy for high-quality videos
- Maintained speed for lower quality inputs
- Intelligent frame selection vs fixed sampling

### 3. Caching Layer Implementation

**Current Issues:**
- No caching of repeated analyses
- Redundant processing of identical videos

**Solutions:**
```python
import hashlib
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=1)

def get_video_hash(video_path):
    """Generate content-based hash for video"""
    with open(video_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...)):
    video_hash = get_video_hash(temp_path)
    
    # Check cache first
    cached_result = redis_client.get(f"analysis:{video_hash}")
    if cached_result:
        return json.loads(cached_result)
    
    # Process and cache result
    result = process_video_file(temp_path)
    redis_client.setex(f"analysis:{video_hash}", 3600, json.dumps(result))
    
    return result
```

**Benefits:**
- Instant response for repeated videos
- Reduced server load
- Better user experience
- Cost optimization

### 4. Background Processing with Celery

**Current Issues:**
- Celery configured but not utilized
- Synchronous processing blocks API

**Solutions:**
```python
@celery.task(bind=True)
def process_video_task(self, job_id, video_path):
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0})
        
        # Pose estimation
        self.update_state(state='PROGRESS', meta={'progress': 30})
        metrics = analyzer.process_video(video_path)
        
        # Risk analysis
        self.update_state(state='PROGRESS', meta={'progress': 70})
        risk = analyze_risk(metrics)
        
        # Complete
        self.update_state(state='SUCCESS', meta={'result': risk})
        return risk
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    job = celery.AsyncResult(job_id)
    return {
        'state': job.state,
        'progress': job.info.get('progress', 0),
        'result': job.info.get('result') if job.state == 'SUCCESS' else None
    }
```

**Benefits:**
- Non-blocking API responses
- Real-time progress updates
- Better resource utilization
- Improved scalability

## Accuracy Improvement Strategy

### 1. Enhanced ML Pipeline

**Current Issues:**
- Small dataset (~280 samples)
- Limited feature set (7 joint angles only)
- No temporal dynamics

### 🎯 CalTennis Dataset Integration (GAME-CHANGING OPPORTUNITY)

**Dataset Opportunity:**
- **11M+ video frames** vs current 280 samples (300x increase)
- Professional tennis players with high-quality footage
- Camera calibration data for accurate 3D analysis
- Potential for transfer learning and pre-training

**Integration Strategy:**

#### A. CalTennis Data Processing Pipeline
```python
# backend/data_processing/caltennis_processor.py
from datasets import load_dataset
import mediapipe as mp
import cv2
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import numpy as np

class CalTennisProcessor:
    def __init__(self, batch_size=1000, max_samples=None):
        self.batch_size = batch_size
        self.max_samples = max_samples
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=2
        )
        
    def load_dataset(self):
        """Load CalTennis dataset"""
        print("Loading CalTennis dataset...")
        self.ds = load_dataset("demalenk/caltennis")
        print(f"Dataset loaded: {self.ds}")
        return self.ds
    
    def process_batch(self, start_idx, end_idx):
        """Process a batch of samples"""
        batch_data = []
        
        for i in tqdm(range(start_idx, min(end_idx, len(self.ds['train'])))):
            sample = self.ds['train'][i]
            
            # Extract frame/image
            frame = sample.get('image') or sample.get('frame')
            if frame is None:
                continue
                
            # Extract pose metrics
            metrics = self.extract_pose_metrics(frame)
            if metrics:
                batch_data.append({
                    'sample_id': i,
                    'action': sample.get('action', 'unknown'),
                    **metrics
                })
        
        return batch_data
    
    def extract_pose_metrics(self, frame):
        """Extract comprehensive pose metrics from frame"""
        # Convert to RGB if needed
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
            
        results = self.pose.process(frame_rgb)
        
        if not results.pose_landmarks:
            return None
        
        landmarks = results.pose_landmarks.landmark
        
        # Extract comprehensive metrics
        metrics = {
            # Basic joint angles
            'left_elbow_angle': self.calculate_angle(
                landmarks[11], landmarks[13], landmarks[15]
            ),
            'right_elbow_angle': self.calculate_angle(
                landmarks[12], landmarks[14], landmarks[16]
            ),
            'left_knee_angle': self.calculate_angle(
                landmarks[23], landmarks[25], landmarks[27]
            ),
            'right_knee_angle': self.calculate_angle(
                landmarks[24], landmarks[26], landmarks[28]
            ),
            'left_shoulder_angle': self.calculate_angle(
                landmarks[13], landmarks[11], landmarks[23]
            ),
            'right_shoulder_angle': self.calculate_angle(
                landmarks[14], landmarks[12], landmarks[24]
            ),
            'hip_angle': self.calculate_angle(
                landmarks[11], 
                [(landmarks[23].x + landmarks[24].x)/2, (landmarks[23].y + landmarks[24].y)/2],
                landmarks[25]
            ),
            # Additional 3D features if available
            'left_elbow_depth': landmarks[13].z,
            'right_elbow_depth': landmarks[14].z,
            'left_knee_depth': landmarks[25].z,
            'right_knee_depth': landmarks[26].z,
            # Confidence scores
            'pose_confidence': np.mean([lm.visibility for lm in landmarks])
        }
        
        return metrics
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three 3D points"""
        a = np.array([a.x, a.y, a.z])
        b = np.array([b.x, b.y, b.z])
        c = np.array([c.x, c.y, c.z])
        
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    def process_full_dataset(self, output_path='caltennis_features.csv'):
        """Process entire dataset in batches"""
        self.load_dataset()
        all_data = []
        
        total_samples = len(self.ds['train'])
        if self.max_samples:
            total_samples = min(total_samples, self.max_samples)
        
        for start_idx in range(0, total_samples, self.batch_size):
            end_idx = min(start_idx + self.batch_size, total_samples)
            print(f"Processing batch {start_idx}-{end_idx}...")
            
            batch_data = self.process_batch(start_idx, end_idx)
            all_data.extend(batch_data)
            
            # Save intermediate results
            if len(all_data) % 5000 == 0:
                df = pd.DataFrame(all_data)
                df.to_csv(output_path, index=False)
                print(f"Saved {len(all_data)} samples to {output_path}")
        
        # Final save
        df = pd.DataFrame(all_data)
        df.to_csv(output_path, index=False)
        print(f"Processing complete! Total samples: {len(all_data)}")
        
        return df
```

#### B. Incremental Training Pipeline
```python
# backend/training/incremental_trainer.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from pathlib import Path
import tempfile
import shutil

class IncrementalTrainer:
    def __init__(self, model_path='risk_model.pkl'):
        self.model_path = Path(model_path)
        self.model = None
        self.feature_columns = None
        self.label_encoder = None
        
    def load_existing_model(self):
        """Load existing model if available"""
        if self.model_path.exists():
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.feature_columns = model_data.get('feature_columns')
            self.label_encoder = model_data.get('label_encoder')
            print("Loaded existing model")
            return True
        return False
    
    def prepare_caltennis_labels(self, df):
        """Create pseudo-labels for CalTennis data using rule-based approach"""
        def assign_risk_score(row):
            """Enhanced rule-based risk scoring"""
            risk_score = 0
            
            # Elbow risks (most common tennis injury)
            if row.get('left_elbow_angle', 180) < 140:
                risk_score += 30
            if row.get('right_elbow_angle', 180) < 140:
                risk_score += 30
                
            # Knee risks
            if row.get('left_knee_angle', 180) < 80:
                risk_score += 25
            if row.get('right_knee_angle', 180) < 80:
                risk_score += 25
                
            # Shoulder risks
            if row.get('left_shoulder_angle', 0) > 160:
                risk_score += 20
            if row.get('right_shoulder_angle', 0) > 160:
                risk_score += 20
                
            # Hip/trunk risks
            hip_angle = row.get('hip_angle', 0)
            if hip_angle < 15 or hip_angle > 65:
                risk_score += 10
                
            return min(risk_score, 100)
        
        df['risk_score'] = df.apply(assign_risk_score, axis=1)
        
        # Convert score to risk level
        def score_to_level(score):
            if score >= 70:
                return 'High'
            elif score >= 40:
                return 'Moderate'
            else:
                return 'Low'
        
        df['risk_level'] = df['risk_score'].apply(score_to_level)
        
        return df
    
    def combine_datasets(self, original_df, caltennis_df):
        """Combine original labeled data with CalTennis pseudo-labeled data"""
        # Mark data sources
        original_df['data_source'] = 'original'
        caltennis_df['data_source'] = 'caltennis_pseudo'
        
        # Ensure consistent feature columns
        common_cols = list(set(original_df.columns) & set(caltennis_df.columns))
        original_df = original_df[common_cols]
        caltennis_df = caltennis_df[common_cols]
        
        # Combine
        combined_df = pd.concat([original_df, caltennis_df], ignore_index=True)
        
        print(f"Combined dataset: {len(original_df)} original + {len(caltennis_df)} CalTennis = {len(combined_df)} total")
        return combined_df
    
    def train_with_caltennis(self, caltennis_path, original_path='tennis_dataset_analysis.csv'):
        """Train model combining original and CalTennis data"""
        # Load original data
        original_df = pd.read_csv(original_path)
        print(f"Loaded original dataset: {len(original_df)} samples")
        
        # Load CalTennis features
        caltennis_df = pd.read_csv(caltennis_path)
        print(f"Loaded CalTennis dataset: {len(caltennis_df)} samples")
        
        # Create pseudo-labels for CalTennis
        caltennis_df = self.prepare_caltennis_labels(caltennis_df)
        
        # Combine datasets
        combined_df = self.combine_datasets(original_df, caltennis_df)
        
        # Prepare features
        feature_cols = [col for col in combined_df.columns 
                       if col not in ['sample_id', 'action', 'risk_level', 'risk_score', 'data_source', 'risk_factors']]
        
        X = combined_df[feature_cols].fillna(0)
        y = combined_df['risk_level']
        
        # Encode labels
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        
        # Train model with weighted classes (give more weight to original data)
        sample_weights = np.where(
            combined_df['data_source'] == 'original', 
            3.0,  # Higher weight for original labeled data
            1.0   # Lower weight for pseudo-labeled data
        )
        
        # Train enhanced model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(
            n_estimators=300,  # More trees for larger dataset
            max_depth=15,      # Deeper trees for more complex patterns
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        print("Training model on combined dataset...")
        model.fit(X, y_encoded, sample_weight=sample_weights)
        
        # Save model
        model_data = {
            'model': model,
            'label_encoder': le,
            'feature_columns': feature_cols,
            'accuracy': None,  # Will be set after evaluation
            'training_samples': len(combined_df),
            'caltennis_samples': len(caltennis_df),
            'original_samples': len(original_df)
        }
        
        # Backup old model
        if self.model_path.exists():
            backup_path = self.model_path.with_suffix('.pkl.backup')
            shutil.copy(self.model_path, backup_path)
            print(f"Backed up old model to {backup_path}")
        
        joblib.dump(model_data, self.model_path)
        print(f"Saved enhanced model to {self.model_path}")
        
        return model_data
```

**Expected Impact of CalTennis Integration:**
- **Dataset Size**: 280 → 100,000+ samples (300x increase)
- **Model Accuracy**: 65% → 85%+ (20% improvement)
- **Generalization**: Better performance on diverse playing styles
- **Feature Quality**: Professional players vs current limited dataset

**Solutions:**

#### A. Feature Engineering
```python
def extract_advanced_features(metrics_sequence):
    """Extract temporal and dynamic features"""
    features = {}
    
    # Static features (current)
    for key in metrics_sequence[0].keys():
        features[f'avg_{key}'] = np.mean([m[key] for m in metrics_sequence])
        features[f'std_{key}'] = np.std([m[key] for m in metrics_sequence])
        features[f'max_{key}'] = np.max([m[key] for m in metrics_sequence])
        features[f'min_{key}'] = np.min([m[key] for m in metrics_sequence])
    
    # Temporal features
    for key in metrics_sequence[0].keys():
        values = [m[key] for m in metrics_sequence]
        # Velocity (rate of change)
        velocity = np.diff(values)
        features[f'avg_velocity_{key}'] = np.mean(np.abs(velocity))
        features[f'max_velocity_{key}'] = np.max(np.abs(velocity))
        
        # Acceleration
        acceleration = np.diff(velocity)
        features[f'avg_acceleration_{key}'] = np.mean(np.abs(acceleration))
    
    # Inter-joint coordination
    features['elbow_knee_correlation'] = np.corrcoef(
        [m['left_elbow_angle'] for m in metrics_sequence],
        [m['left_knee_angle'] for m in metrics_sequence]
    )[0,1]
    
    return features
```

#### B. Ensemble Models
```python
from sklearn.ensemble import VotingClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier

def create_ensemble_model():
    """Create ensemble of different model types"""
    models = [
        ('rf', RandomForestClassifier(n_estimators=200, max_depth=10)),
        ('xgb', XGBClassifier(n_estimators=100, max_depth=6)),
        ('gb', GradientBoostingClassifier(n_estimators=100, max_depth=5))
    ]
    
    ensemble = VotingClassifier(
        estimators=models,
        voting='soft'  # Use probability averages
    )
    
    return ensemble
```

#### C. Data Augmentation
```python
def augment_tennis_data(metrics):
    """Generate synthetic training data"""
    augmented = [metrics]
    
    # Add noise to joint angles
    for noise_level in [0.5, 1.0, 1.5]:
        noisy = {k: v + np.random.normal(0, noise_level) for k, v in metrics.items()}
        augmented.append(noisy)
    
    # Small angle variations
    for angle_offset in [-2, -1, 1, 2]:
        offset = {k: v + angle_offset for k, v in metrics.items()}
        augmented.append(offset)
    
    return augmented
```

### 2. Model Monitoring and Retraining

**Current Issues:**
- No model performance monitoring
- No continuous learning pipeline
- No A/B testing capability

**Solutions:**
```python
class ModelMonitor:
    def __init__(self):
        self.predictions = []
        self.user_feedback = []
    
    def log_prediction(self, metrics, prediction, user_feedback=None):
        """Log prediction and optional user feedback"""
        self.predictions.append({
            'timestamp': datetime.now(),
            'metrics': metrics,
            'prediction': prediction,
            'feedback': user_feedback
        })
    
    def calculate_drift(self):
        """Calculate model drift over time"""
        recent = self.predictions[-100:]
        historical = self.predictions[:-100]
        
        # Compare prediction distributions
        recent_scores = [p['prediction']['risk_score'] for p in recent]
        historical_scores = [p['prediction']['risk_score'] for p in historical]
        
        drift = ks_2samp(recent_scores, historical_scores).statistic
        return drift
    
    def should_retrain(self, threshold=0.2):
        """Check if model should be retrained"""
        drift = self.calculate_drift()
        feedback_accuracy = self.calculate_feedback_accuracy()
        
        return drift > threshold or feedback_accuracy < 0.8
```

### 3. Advanced Pose Estimation

**Current Issues:**
- Single MediaPipe model
- No confidence-based filtering
- Missing 3D pose information

**Solutions:**
```python
class AdvancedPoseAnalyzer:
    def __init__(self):
        # Use multiple MediaPipe models for robustness
        self.pose_landmarker = mp_pose.Pose(
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.7
        )
    
    def process_with_confidence(self, frame):
        """Process frame with confidence scoring"""
        results = self.pose_landmarker.process(frame)
        
        if not results.pose_landmarks:
            return None, 0.0
        
        # Calculate overall confidence
        confidences = [lm.visibility for lm in results.pose_landmarks.landmark]
        avg_confidence = np.mean(confidences)
        
        if avg_confidence < 0.6:
            return None, avg_confidence
        
        metrics = self.extract_metrics(results.pose_landmarks)
        return metrics, avg_confidence
    
    def process_video_smart(self, video_path):
        """Smart frame selection based on quality"""
        cap = cv2.VideoCapture(video_path)
        high_quality_frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            metrics, confidence = self.process_with_confidence(frame)
            if metrics and confidence > 0.8:
                high_quality_frames.append(metrics)
            
            if len(high_quality_frames) >= 30:  # Target 30 high-quality frames
                break
        
        cap.release()
        return high_quality_frames
```

## Infrastructure Improvements

### 1. Containerization and Orchestration

**Current Issues:**
- No containerization
- Manual deployment process
- No auto-scaling

**Solutions:**

#### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with gunicorn for production
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

#### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: injury-risk-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: injury-risk-api
  template:
    metadata:
      labels:
        app: injury-risk-api
    spec:
      containers:
      - name: api
        image: injury-risk-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
---
apiVersion: v1
kind: Service
metadata:
  name: injury-risk-api-service
spec:
  selector:
    app: injury-risk-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 2. Monitoring and Observability

**Current Issues:**
- No monitoring
- No alerting
- No performance tracking

**Solutions:**
```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'API request duration')
pose_processing_time = Histogram('pose_processing_duration_seconds', 'Pose processing time')
model_prediction_time = Histogram('model_prediction_duration_seconds', 'Model prediction time')

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    request_count.inc()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 3. Database and Storage

**Current Issues:**
- No persistent storage
- No user data tracking
- No analysis history

**Solutions:**
```python
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String)  # Anonymous user ID
    video_hash = Column(String)  # For deduplication
    timestamp = Column(DateTime)
    risk_level = Column(String)
    risk_score = Column(Float)
    metrics = Column(String)  # JSON string
    feedback = Column(String)  # User feedback (optional)

class UserFeedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer)
    feedback_type = Column(String)  # 'helpful', 'not_helpful', 'inaccurate'
    comments = Column(String)
    timestamp = Column(DateTime)
```

### 4. CI/CD Pipeline

**Current Issues:**
- No automated testing
- No automated deployment
- Manual quality checks

**Solutions:**
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: docker build -t injury-risk-api:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push injury-risk-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/injury-risk-api api=injury-risk-api:${{ github.sha }}
```

## Implementation Roadmap

### Phase 0: CalTennis Dataset Integration (Week 1-2) 
**Priority: CRITICAL - GAME CHANGER**

1. **CalTennis Dataset Setup**
   - Install datasets library and dependencies
   - Load and explore CalTennis dataset structure
   - Set up batch processing pipeline
   - **Impact**: 300x dataset size increase (280 → 100,000+ samples)

2. **Process CalTennis Data**
   - Implement CalTennisProcessor for batch processing
   - Extract pose features from 11M+ frames
   - Create pseudo-labels using enhanced rule-based approach
   - **Impact**: Massive training data availability

3. **Train Enhanced Model**
   - Implement IncrementalTrainer for combined dataset training
   - Weight original labeled data higher than pseudo-labels
   - Train ensemble model on 100,000+ samples
   - **Impact**: 20%+ accuracy improvement (65% → 85%+)

4. **Expert Labeling Workflow**
   - Create diverse labeling batches from CalTennis data
   - Set up workflow for sports physiotherapist labeling
   - Integrate expert labels back into training pipeline
   - **Impact**: Ground truth labels for continuous improvement

### Phase 1: Critical Performance Fixes (Week 3-4)
**Priority: HIGH**

1. **Fix Video Upload Timeout**
   - Migrate from base64 to multipart FormData
   - Implement proper timeout handling
   - Add progress tracking
   - **Impact**: Immediate user experience improvement

2. **Enable Celery Background Processing**
   - Configure Redis properly
   - Implement async job processing
   - Add job status endpoints
   - **Impact**: Non-blocking API, better scalability

3. **Add Basic Caching**
   - Implement Redis caching
   - Add video hash-based deduplication
   - Set appropriate TTL values
   - **Impact**: Reduced server load, faster repeated analyses

### Phase 2: Advanced Accuracy Enhancements (Week 5-6)
**Priority: HIGH**

1. **Advanced Feature Engineering**
   - Implement temporal features (velocity, acceleration) on CalTennis data
   - Add inter-joint coordination metrics
   - Extract statistical features (mean, std, min, max)
   - **Impact**: Additional 10-15% accuracy improvement on top of CalTennis gains

2. **Enhanced Model Ensemble**
   - Implement XGBoost + RandomForest ensemble on large dataset
   - Add GradientBoosting classifier
   - Implement soft voting mechanism
   - **Impact**: 5-10% additional accuracy improvement

3. **Data Augmentation**
   - Implement training data augmentation for CalTennis data
   - Add noise injection
   - Create angle variations
   - **Impact**: Better generalization, reduced overfitting

### Phase 3: Infrastructure Scaling (Week 7-8)
**Priority: MEDIUM**

1. **Containerization**
   - Create Docker configuration
   - Optimize image size
   - Add multi-stage builds
   - **Impact**: Consistent deployments, easier scaling

2. **Kubernetes Deployment**
   - Create K8s manifests
   - Configure auto-scaling
   - Set up load balancing
   - **Impact**: Horizontal scaling, high availability

3. **Monitoring Setup**
   - Implement Prometheus metrics
   - Add Grafana dashboards
   - Set up alerting rules
   - **Impact**: Visibility into system health

### Phase 4: Advanced Features (Week 9-10)
**Priority: MEDIUM**

1. **Advanced Pose Estimation**
   - Implement confidence-based filtering
   - Add smart frame selection
   - Use higher quality MediaPipe model
   - **Impact**: Better pose accuracy, reduced noise

2. **Model Monitoring**
   - Implement prediction logging
   - Add drift detection
   - Create retraining triggers
   - **Impact**: Continuous model improvement

3. **Database Integration**
   - Set up PostgreSQL
   - Implement analysis history
   - Add user feedback collection
   - **Impact**: Data-driven improvements

### Phase 5: Optimization and Polish (Week 11-12)
**Priority: LOW**

1. **Performance Tuning**
   - Optimize database queries
   - Implement connection pooling
   - Add response compression
   - **Impact**: Faster response times

2. **Security Hardening**
   - Add rate limiting
   - Implement input validation
   - Add authentication/authorization
   - **Impact**: Security compliance

3. **Documentation and Testing**
   - Add comprehensive API docs
   - Implement integration tests
   - Create deployment guides
   - **Impact**: Maintainability, reliability

## Expected Improvements

### Performance Metrics
- **Video Upload Time**: 60% reduction (3 min → 1.2 min)
- **API Response Time**: 80% improvement (blocking → async)
- **Server Throughput**: 5x increase (single → multi-worker)
- **Cache Hit Rate**: 30% for repeated analyses

### Accuracy Metrics (REVISED - CalTennis Impact)
- **Model Accuracy**: 35-40% improvement (65% → 85-90% with CalTennis)
- **Dataset Size**: 300x increase (280 → 100,000+ samples)
- **False Positive Rate**: 50% reduction (better calibration + more data)
- **False Negative Rate**: 45% reduction (enhanced features + larger dataset)
- **Generalization**: Significant improvement on diverse playing styles
- **User Satisfaction**: 50% improvement (faster + much more accurate)

### Infrastructure Metrics
- **System Availability**: 99.9% (Kubernetes HA)
- **Auto-scaling**: 0-10 instances based on load
- **Deployment Time**: 5 minutes (CI/CD)
- **Monitoring Coverage**: 100% of critical components

## Risk Assessment and Mitigation

### Technical Risks
1. **Model Performance Degradation**
   - *Risk*: New features may overfit
   - *Mitigation*: Cross-validation, A/B testing, gradual rollout

2. **Infrastructure Complexity**
   - *Risk*: K8s complexity may cause issues
   - *Mitigation*: Start with simple deployment, phased rollout

3. **Performance Regression**
   - *Risk*: New features may slow down system
   - *Mitigation*: Performance benchmarks, load testing

### Operational Risks
1. **Downtime During Migration**
   - *Risk*: Users may experience downtime
   - *Mitigation*: Blue-green deployment, canary releases

2. **Increased Costs**
   - *Risk*: Cloud infrastructure costs may increase
   - *Mitigation*: Auto-scaling, spot instances, cost monitoring

3. **Data Privacy**
   - *Risk*: User video data privacy concerns
   - *Mitigation*: Data encryption, retention policies, compliance

## Success Criteria

### Technical Success
- [ ] Video upload time < 2 minutes for 15s videos
- [ ] API response time < 500ms for cached results
- [ ] Model accuracy > 85% on test set (with CalTennis integration)
- [ ] Dataset size > 100,000 samples (CalTennis integration)
- [ ] System uptime > 99.9%
- [ ] Auto-scaling handles 10x load spikes

### Business Success
- [ ] User satisfaction score > 4.5/5
- [ ] Analysis completion rate > 95%
- [ ] Cost per analysis < $0.10
- [ ] Time to deploy new features < 1 day
- [ ] Support ticket volume < 5% of users

## Conclusion

This architecture improvement plan addresses the critical bottlenecks in the current system while providing a clear roadmap for enhancement. The phased approach allows for incremental improvements with minimal risk, while the expected performance and accuracy gains will significantly improve user experience and system reliability.

The focus on containerization, monitoring, and continuous improvement ensures the system can scale to meet growing demand while maintaining high quality standards.