"""
ml_risk_engine.py

ML-powered risk engine that uses the trained RandomForest model
to predict injury risk from joint angle metrics.

Usage:
    from app.ml_risk_engine import MLRiskEngine
    
    # Load model once at startup
    MLRiskEngine.load_model()
    
    # Predict risk from metrics
    result = MLRiskEngine.predict_risk(metrics)
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any
from warnings import warn

# Define the expected feature order (must match training)
FEATURES = [
    'left_elbow_angle',
    'right_elbow_angle',
    'left_knee_angle',
    'right_knee_angle',
    'left_shoulder_angle',
    'right_shoulder_angle',
    'hip_angle'
]

# Map class indices to risk levels (as encoded in training)
CLASS_MAP = {
    0: 'High',
    1: 'Low',
    2: 'Moderate'
}

# Recommendations based on risk level + most influential joint
RECOMMENDATIONS_MAP = {
    'High': {
        'elbow': [
            {
                "id": "r0",
                "title": "Reduce training intensity",
                "detail": "High elbow flexion risk detected. Reduce stroke intensity and consult a sports physiotherapist for a biomechanical assessment."
            },
            {
                "id": "r1",
                "title": "Eccentric wrist strengthening",
                "detail": "3 sets of 12 eccentric wrist curls, slow lowering phase, 3x per week to build tendon resilience."
            }
        ],
        'knee': [
            {
                "id": "r0",
                "title": "Reduce deep knee loading",
                "detail": "High knee flexion load detected. Focus on quad and glute strengthening with controlled lunges (keep knee behind toes)."
            },
            {
                "id": "r1",
                "title": "Patellar tendon care",
                "detail": "Apply ice after activity and perform isometric knee extension holds (45s, 5 reps) to manage patellar tendon stress."
            }
        ],
        'shoulder': [
            {
                "id": "r0",
                "title": "Rotator cuff strengthening",
                "detail": "External rotation with bands, 3 sets of 15 reps. Essential for overhead athletes to prevent impingement."
            },
            {
                "id": "r1",
                "title": "Shoulder mobility work",
                "detail": "Incorporate sleeper stretches and cross-body stretches, 30s each side, before and after play."
            }
        ],
        'default': [
            {
                "id": "r0",
                "title": "Consult a physiotherapist",
                "detail": "Your movement patterns show elevated injury risk. A professional assessment can identify specific corrective exercises."
            },
            {
                "id": "r1",
                "title": "Active recovery focus",
                "detail": "Incorporate light mobility work and active recovery sessions between training days."
            }
        ]
    },
    'Moderate': {
        'default': [
            {
                "id": "r0",
                "title": "Incorporate targeted strengthening",
                "detail": "Add eccentric exercises and controlled dynamic stretches for the flagged joint areas 2-3x per week."
            },
            {
                "id": "r1",
                "title": "Monitor your form",
                "detail": "Record and review your stroke technique. Small adjustments to joint angles can significantly reduce injury risk."
            }
        ]
    },
    'Low': {
        'default': [
            {
                "id": "r0",
                "title": "Continue your warm-up routine",
                "detail": "Your movement looks good! Maintain your current warm-up and cool-down routine to stay injury-free."
            },
            {
                "id": "r1",
                "title": "Preventive maintenance",
                "detail": "Regular foam rolling and stretching of the forearms, shoulders, and legs will help sustain healthy movement patterns."
            }
        ]
    }
}


def _get_joint_category(metrics: Dict[str, float]) -> str:
    """
    Determine which joint category is most at risk based on angle deviations.
    Uses the same thresholds as the rule-based engine for factor suggestions.
    """
    worst_joint = 'default'
    worst_deviation = 0.0

    # Elbow: check if below 140°
    for side in ['left', 'right']:
        angle = metrics.get(f'{side}_elbow_angle', 180)
        deviation = max(0, 140 - angle)
        if deviation > worst_deviation:
            worst_deviation = deviation
            worst_joint = 'elbow'

    # Knee: check if below 80°
    for side in ['left', 'right']:
        angle = metrics.get(f'{side}_knee_angle', 180)
        deviation = max(0, 80 - angle)
        if deviation > worst_deviation:
            worst_deviation = deviation
            worst_joint = 'knee'

    # Shoulder: check if above 160°
    for side in ['left', 'right']:
        angle = metrics.get(f'{side}_shoulder_angle', 0)
        deviation = max(0, angle - 160)
        if deviation > worst_deviation:
            worst_deviation = deviation
            worst_joint = 'shoulder'

    return worst_joint


def get_recommendations(risk_level: str, metrics: Dict[str, float]) -> list:
    """
    Generate structured recommendations based on risk level and joint angles.
    """
    level_map = RECOMMENDATIONS_MAP.get(risk_level, RECOMMENDATIONS_MAP['Low'])
    joint_category = _get_joint_category(metrics)
    
    # Try joint-specific recs first, fall back to default
    joint_recs = level_map.get(joint_category)
    if joint_recs:
        return joint_recs[:3]  # max 3 recommendations
    
    return level_map['default'][:3]


class MLRiskEngine:
    """ML-powered risk prediction engine."""
    
    _model = None
    _label_encoder = None
    _feature_columns = None

    @classmethod
    def load_model(cls, model_path=None):
        """Load the trained model (call once at startup)."""
        if model_path is None:
            # Default path relative to this file: backend/app/ -> backend/
            base_dir = Path(__file__).parent.parent
            model_path = base_dir / 'risk_model.pkl'
        
        if not model_path.exists():
            print(f"⚠️ ML model not found at {model_path}. Rule-based engine will be used.")
            cls._model = None
            return False
        
        try:
            model_data = joblib.load(model_path)
            cls._model = model_data['model']
            cls._label_encoder = model_data['label_encoder']
            cls._feature_columns = model_data.get('feature_columns', FEATURES)
            print(f"✅ ML model loaded from {model_path}")
            return True
        except Exception as exc:
            # Keep API available even if serialized artifact is incompatible.
            cls._model = None
            cls._label_encoder = None
            cls._feature_columns = FEATURES
            warn(
                f"ML model could not be loaded from {model_path}: {exc}. "
                "Falling back to rule-based engine. "
                "Re-train model with current dependencies via: python train_model.py"
            )
            return False

    @classmethod
    def is_available(cls) -> bool:
        """Check if the ML model is loaded and available."""
        return cls._model is not None

    @classmethod
    def predict_risk(cls, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict injury risk from joint angles using the trained ML model.
        
        Args:
            metrics: Dict with keys matching FEATURES (e.g., 'left_elbow_angle', 'right_elbow_angle', etc.)
            
        Returns:
            Dict with:
                - 'risk_level': str ('Low', 'Moderate', 'High')
                - 'risk_score': int (0-100)
                - 'predicted_class': int
                - 'probabilities': dict with confidence scores per class
                - 'primary_risk_factors': list of risk factor descriptions
                - 'recommendations': list of recommendation dicts
                - 'flagged_joint': str (joint with highest risk contribution)
                - 'flagged_label': str (human-readable joint name)
        """
        if cls._model is None:
            raise RuntimeError("ML model not loaded. Call load_model() first.")

        # Build feature vector in the correct order
        feature_vector = np.array([[metrics.get(f, 0.0) for f in cls._feature_columns]])
        
        # Get class probabilities
        probs = cls._model.predict_proba(feature_vector)[0]  # array of 3 probabilities
        pred_class = int(np.argmax(probs))
        
        # Decode risk level
        if cls._label_encoder:
            risk_level = cls._label_encoder.inverse_transform([pred_class])[0]
        else:
            risk_level = CLASS_MAP[pred_class]
        
        # Risk score: scaled confidence of the predicted class (0-100)
        risk_score = int(round(probs[pred_class] * 100))
        
        # Determine flagged joint from feature importances * deviations
        flagged_joint, flagged_label = cls._get_flagged_joint(metrics)
        
        # Generate risk factors
        risk_factors = cls._generate_risk_factors(metrics, risk_level)
        
        # Generate recommendations
        recommendations = get_recommendations(risk_level, metrics)
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'propabilities': {
                'High': float(probs[0]),
                'Low': float(probs[1]),
                'Moderate': float(probs[2])
            },
            'flagged_joint': flagged_joint,
            'flagged_label': flagged_label,
            'primary_risk_factors': risk_factors,
            'recommendations': recommendations,
        }

    @classmethod
    def _get_flagged_joint(cls, metrics: Dict[str, float]):
        """Determine which joint is most at risk using angle thresholds."""
        joint_scores = {}
        
        # Elbow risk: angle < 140° indicates hyperflexion
        for side in ['left', 'right']:
            angle = metrics.get(f'{side}_elbow_angle', 180)
            if angle < 140:
                score = (140 - angle) * 1.5
                joint_scores[f'{side}_elbow'] = score
        
        # Knee risk: angle < 80° indicates deep bend
        for side in ['left', 'right']:
            angle = metrics.get(f'{side}_knee_angle', 180)
            if angle < 80:
                score = (80 - angle) * 1.5
                joint_scores[f'{side}_knee'] = score
        
        # Shoulder risk: angle > 160° indicates impingement
        for side in ['left', 'right']:
            angle = metrics.get(f'{side}_shoulder_angle', 0)
            if angle > 160:
                score = (angle - 160) * 1.5
                joint_scores[f'{side}_shoulder'] = score
        
        # Hip risk
        hip_angle = metrics.get('hip_angle', 0)
        if hip_angle < 15 or hip_angle > 65:
            deviation = min(abs(hip_angle - 15), abs(hip_angle - 65))
            joint_scores['hip'] = deviation
        
        if not joint_scores:
            return 'right_elbow', 'Right elbow'
        
        worst_joint = max(joint_scores, key=joint_scores.get)
        label_map = {
            'left_elbow': 'Left elbow', 'right_elbow': 'Right elbow',
            'left_knee': 'Left knee', 'right_knee': 'Right knee',
            'left_shoulder': 'Left shoulder', 'right_shoulder': 'Right shoulder',
            'hip': 'Hip',
        }
        return worst_joint, label_map.get(worst_joint, worst_joint.replace('_', ' ').title())

    @classmethod
    def _generate_risk_factors(cls, metrics: Dict[str, float], risk_level: str) -> list:
        """Generate risk factor descriptions based on angle deviations."""
        risk_factors = []
        
        # Elbow checks
        for side in ['left', 'right']:
            angle = metrics.get(f'{side}_elbow_angle', 180)
            if angle < 140:
                label = 'Left' if side == 'left' else 'Right'
                risk_factors.append({
                    "id": f"{side}_elbow",
                    "title": f"{label} elbow overly flexed",
                    "detail": f"Angle dropped to {angle:.0f}° during contact, below the 140° comfort range. Sustained sharp flexion under load is linked to lateral epicondylitis (tennis elbow)."
                })
        
        # Knee checks
        for side in ['left', 'right']:
            angle = metrics.get(f'{side}_knee_angle', 180)
            if angle < 80:
                label = 'Left' if side == 'left' else 'Right'
                risk_factors.append({
                    "id": f"{side}_knee",
                    "title": f"{label} knee deep bend",
                    "detail": f"Knee angle reached {angle:.0f}°, well below the 80° threshold. Deep flexion under load can strain the patellar tendon."
                })
        
        # Shoulder checks
        for side in ['left', 'right']:
            angle = metrics.get(f'{side}_shoulder_angle', 0)
            if angle > 160:
                label = 'Left' if side == 'left' else 'Right'
                risk_factors.append({
                    "id": f"{side}_shoulder",
                    "title": f"{label} shoulder in vulnerable position",
                    "detail": f"Shoulder angle measured at {angle:.0f}°, exceeding the 160° safe limit. Overhead positioning beyond this range increases impingement risk."
                })
        
        # Hip check
        hip_angle = metrics.get('hip_angle', 0)
        if hip_angle < 15 or hip_angle > 65:
            risk_factors.append({
                "id": "trunk",
                "title": "Trunk leaning excessively",
                "detail": f"Torso lean measured at {hip_angle:.0f}°, outside the 15°–65° tennis-specific range. Can shift load onto the lower back during the swing."
            })
        
        if not risk_factors and risk_level != 'Low':
            # Model predicted risk but no specific angles triggered — add general factor
            risk_factors.append({
                "id": "combined_movement",
                "title": "Combined movement pattern risk",
                "detail": "The ML model identified elevated risk from the overall joint angle combination, even though individual angles appear within normal ranges."
            })
        
        return risk_factors

