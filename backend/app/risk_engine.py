from typing import List, Dict, Any, Tuple
from app.config import settings

# Joint label mapping for human-readable names
JOINT_LABELS = {
    "left_elbow": "Left elbow",
    "right_elbow": "Right elbow",
    "left_knee": "Left knee",
    "right_knee": "Right knee",
    "left_shoulder": "Left shoulder",
    "right_shoulder": "Right shoulder",
    "hip": "Hip",
}

FLAGGED_JOINT_MAP = {
    "elbow": "right_elbow",
    "knee": "right_knee",
    "shoulder": "right_shoulder",
    "trunk": "hip",
}

class RiskEngine:
    # Define risk rules per sport (expandable)
    # For tennis, we flag extreme angles that correlate with common injuries
    @staticmethod
    def evaluate_metrics(metrics: Dict[str, float]) -> Dict[str, Any]:
        risk_factors = []
        risk_score = 0
        flagged_joint = None
        max_factor_score = 0

        # Tennis elbow: sharp elbow angle on forehand/backhand (we check both sides)
        if metrics.get("left_elbow_angle", 180) < 140:
            risk_factors.append({
                "id": "left_elbow",
                "title": "Left elbow overly flexed",
                "detail": f"Angle dropped to {metrics.get('left_elbow_angle', 0):.0f}° during contact, below the 140° comfort range. Sustained sharp flexion under load is linked to lateral epicondylitis (tennis elbow)."
            })
            risk_score += 30
            if 30 > max_factor_score:
                max_factor_score = 30
                flagged_joint = "left_elbow"

        if metrics.get("right_elbow_angle", 180) < 140:
            risk_factors.append({
                "id": "right_elbow",
                "title": "Right elbow overly flexed",
                "detail": f"Angle dropped to {metrics.get('right_elbow_angle', 0):.0f}° during contact, below the 140° comfort range. Sustained sharp flexion under load is linked to lateral epicondylitis (tennis elbow)."
            })
            risk_score += 30
            if 30 > max_factor_score:
                max_factor_score = 30
                flagged_joint = "right_elbow"

        # Knee stress: deep lunge angle (knee < 90°)
        if metrics.get("left_knee_angle", 180) < 80:
            risk_factors.append({
                "id": "left_knee",
                "title": "Left knee deep bend",
                "detail": f"Knee angle reached {metrics.get('left_knee_angle', 0):.0f}°, well below the 80° threshold. Deep flexion under load can strain the patellar tendon."
            })
            risk_score += 25
            if 25 > max_factor_score:
                max_factor_score = 25
                flagged_joint = "left_knee"

        if metrics.get("right_knee_angle", 180) < 80:
            risk_factors.append({
                "id": "right_knee",
                "title": "Right knee deep bend",
                "detail": f"Knee angle reached {metrics.get('right_knee_angle', 0):.0f}°, well below the 80° threshold. Deep flexion under load can strain the patellar tendon."
            })
            risk_score += 25
            if 25 > max_factor_score:
                max_factor_score = 25
                flagged_joint = "right_knee"

        # Shoulder impingement: overhead serve with excessive shoulder angle (>160°)
        if metrics.get("left_shoulder_angle", 0) > 160:
            risk_factors.append({
                "id": "left_shoulder",
                "title": "Left shoulder in vulnerable position",
                "detail": f"Shoulder angle measured at {metrics.get('left_shoulder_angle', 0):.0f}°, exceeding the 160° safe limit. Overhead positioning beyond this range increases impingement risk."
            })
            risk_score += 20
            if 20 > max_factor_score:
                max_factor_score = 20
                flagged_joint = "left_shoulder"

        if metrics.get("right_shoulder_angle", 0) > 160:
            risk_factors.append({
                "id": "right_shoulder",
                "title": "Right shoulder in vulnerable position",
                "detail": f"Shoulder angle measured at {metrics.get('right_shoulder_angle', 0):.0f}°, exceeding the 160° safe limit. Overhead positioning beyond this range increases impingement risk."
            })
            risk_score += 20
            if 20 > max_factor_score:
                max_factor_score = 20
                flagged_joint = "right_shoulder"

        # Hip/trunk lean – torso rotation during tennis strokes (forehand, serve)
        # Tennis-specific: natural trunk rotation ranges 20°–70°; outside this is excessive
        hip_angle = metrics.get("hip_angle", 0)
        if hip_angle < 15 or hip_angle > 65:
            risk_factors.append({
                "id": "trunk",
                "title": "Trunk leaning excessively",
                "detail": f"Torso lean measured at {hip_angle:.0f}°, outside the 15°–65° tennis-specific range. Can shift load onto the lower back during the swing."
            })
            risk_score += 10  # Lower weight than elbow/knee — trunk rotation is less directly injurious
            if 10 > max_factor_score:
                max_factor_score = 10
                flagged_joint = "hip"

        # Determine risk level
        if risk_score >= settings.RISK_THRESHOLDS["HIGH"]:
            level = "High"
        elif risk_score >= settings.RISK_THRESHOLDS["MODERATE"]:
            level = "Moderate"
        else:
            level = "Low"

        # Default flagged joint if none triggered
        if not flagged_joint and risk_factors:
            flagged_joint = risk_factors[0]["id"]
        elif not flagged_joint:
            flagged_joint = "right_elbow"

        flagged_label = JOINT_LABELS.get(flagged_joint, flagged_joint.replace("_", " ").title())

        return {
            "risk_score": min(risk_score, 100),
            "risk_level": level,
            "risk_factors": risk_factors,
            "flagged_joint": flagged_joint,
            "flagged_label": flagged_label,
        }

    @staticmethod
    def generate_recommendations(risk_factors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Provide corrective exercises based on identified risks."""
        recs = []
        rec_id = 0

        for factor in risk_factors:
            factor_id = factor.get("id", "")
            factor_title = factor.get("title", "").lower()

            if "elbow" in factor_id or "elbow" in factor_title:
                recs.append({
                    "id": f"r{rec_id}",
                    "title": "Eccentric wrist curls",
                    "detail": "3 sets of 12, slow lowering phase, 3x per week. Builds tendon resilience in the forearm extensors."
                })
                rec_id += 1
                recs.append({
                    "id": f"r{rec_id}",
                    "title": "Forearm stretches",
                    "detail": "Hold wrist flexor and extensor stretches for 30s each side before and after play."
                })
                rec_id += 1

            if "knee" in factor_id or "knee" in factor_title:
                recs.append({
                    "id": f"r{rec_id}",
                    "title": "Quad and glute strengthening",
                    "detail": "Strengthen quads, glutes, and hamstrings. Practice lunges with proper form keeping knee behind toes."
                })
                rec_id += 1

            if "shoulder" in factor_id or "shoulder" in factor_title:
                recs.append({
                    "id": f"r{rec_id}",
                    "title": "Rotator cuff strengthening",
                    "detail": "Incorporate external rotation with bands, 3 sets of 15 reps. Essential for overhead athletes."
                })
                rec_id += 1

            if "trunk" in factor_id or "hip" in factor_id or "back" in factor_title or "trunk" in factor_title:
                recs.append({
                    "id": f"r{rec_id}",
                    "title": "Core stability exercises",
                    "detail": "Planks and anti-rotation holds, 2x per week, to reduce reliance on trunk lean for power."
                })
                rec_id += 1

        if not recs:
            recs.append({
                "id": "r0",
                "title": "Continue your warm-up routine",
                "detail": "Your movement looks good! Maintain your current warm-up and cool-down routine to stay injury-free."
            })

        # Limit to 5 recommendations max
        return recs[:5]

