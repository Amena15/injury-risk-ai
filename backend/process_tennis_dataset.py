"""
process_tennis_dataset.py

Processes the Tennis Player Actions Dataset for Human Pose Estimation.
Extracts keypoints from COCO-format JSON annotations,
computes joint angles, runs the RiskEngine, and saves results to CSV.

Dataset keypoint format (18 keypoints, custom ordering):
    0: nose         1: left_eye      2: right_eye
    3: left_ear     4: right_ear     5: left_shoulder
    6: right_shoulder  7: left_elbow  8: right_elbow
    9: left_wrist   10: right_wrist  11: left_hip
    12: right_hip   13: left_knee    14: right_knee
    15: left_ankle  16: right_ankle  17: neck
"""

import os
import json
import csv
import sys
import numpy as np

# Add parent directory so we can import from app/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.risk_engine import RiskEngine

# --- Configuration ---
# Path to the Dataset folder (relative to this script's location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, '..', 'Dataset',
                            'Tennis Player Actions Dataset for Human Pose Estimation')

# Keypoint names for reference (dataset ordering)
KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle", "neck"
]

# Keypoint indices (for readability)
KP = {
    'nose': 0, 'left_eye': 1, 'right_eye': 2,
    'left_ear': 3, 'right_ear': 4,
    'left_shoulder': 5, 'right_shoulder': 6,
    'left_elbow': 7, 'right_elbow': 8,
    'left_wrist': 9, 'right_wrist': 10,
    'left_hip': 11, 'right_hip': 12,
    'left_knee': 13, 'right_knee': 14,
    'left_ankle': 15, 'right_ankle': 16,
    'neck': 17,
}


def get_keypoint(keypoints, idx):
    """
    Extract (x, y, visibility) from a COCO-format keypoints array.
    COCO format: [x1, y1, v1, x2, y2, v2, ...]
    visibility: 0=not labeled, 1=labeled but not visible, 2=labeled and visible
    """
    x = keypoints[idx * 3]
    y = keypoints[idx * 3 + 1]
    v = keypoints[idx * 3 + 2]
    return (x, y, v)


def angle_between_points(a, b, c):
    """
    Calculate the angle (in degrees) at point b, formed by points a-b-c.
    Returns 0.0 if points are degenerate (zero-length segments).
    """
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    denominator = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denominator < 1e-8:
        return 0.0
    cos_angle = np.dot(ba, bc) / denominator
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def compute_metrics(keypoints):
    """
    Compute joint angle metrics from the dataset's 18 keypoints.

    Returns a dict matching the keys expected by RiskEngine.evaluate_metrics():
      - left_elbow_angle, right_elbow_angle
      - left_knee_angle, right_knee_angle
      - left_shoulder_angle, right_shoulder_angle
      - hip_angle

    Returns None if too many keypoints are missing (any of the main 7 joints invisible).
    """
    # Extract all keypoints with visibility
    kp_data = {}
    for name, idx in KP.items():
        kp_data[name] = get_keypoint(keypoints, idx)

    # Map to named tuples for readability
    def xy(name):
        return (kp_data[name][0], kp_data[name][1])

    def visible(name):
        return kp_data[name][2] >= 2

    # We need these joints to be visible for meaningful metrics
    required_joints = [
        'right_shoulder', 'right_elbow', 'right_wrist',
        'left_shoulder', 'left_elbow', 'left_wrist',
        'right_hip', 'right_knee', 'right_ankle',
        'left_hip', 'left_knee', 'left_ankle',
        'neck'
    ]

    for joint in required_joints:
        if not visible(joint):
            return None

    # --- Compute Angles ---

    # Right elbow angle: right_shoulder -> right_elbow -> right_wrist
    right_elbow_angle = angle_between_points(
        xy('right_shoulder'), xy('right_elbow'), xy('right_wrist')
    )

    # Left elbow angle: left_shoulder -> left_elbow -> left_wrist
    left_elbow_angle = angle_between_points(
        xy('left_shoulder'), xy('left_elbow'), xy('left_wrist')
    )

    # Right knee angle: right_hip -> right_knee -> right_ankle
    right_knee_angle = angle_between_points(
        xy('right_hip'), xy('right_knee'), xy('right_ankle')
    )

    # Left knee angle: left_hip -> left_knee -> left_ankle
    left_knee_angle = angle_between_points(
        xy('left_hip'), xy('left_knee'), xy('left_ankle')
    )

    # Right shoulder angle: right_elbow -> right_shoulder -> right_hip
    right_shoulder_angle = angle_between_points(
        xy('right_elbow'), xy('right_shoulder'), xy('right_hip')
    )

    # Left shoulder angle: left_elbow -> left_shoulder -> left_hip
    left_shoulder_angle = angle_between_points(
        xy('left_elbow'), xy('left_shoulder'), xy('left_hip')
    )

    # Hip angle (torso lean): neck -> hip_center -> right_knee
    # Use midpoint of left_hip and right_hip as the hip center
    hip_center_x = (xy('left_hip')[0] + xy('right_hip')[0]) / 2.0
    hip_center_y = (xy('left_hip')[1] + xy('right_hip')[1]) / 2.0
    hip_center = (hip_center_x, hip_center_y)

    hip_angle = angle_between_points(
        xy('neck'), hip_center, xy('right_knee')
    )

    metrics = {
        'left_elbow_angle': left_elbow_angle,
        'right_elbow_angle': right_elbow_angle,
        'left_knee_angle': left_knee_angle,
        'right_knee_angle': right_knee_angle,
        'left_shoulder_angle': left_shoulder_angle,
        'right_shoulder_angle': right_shoulder_angle,
        'hip_angle': hip_angle,
    }

    return metrics


def main():
    annotations_dir = os.path.join(DATASET_PATH, 'annotations')

    if not os.path.isdir(annotations_dir):
        print(f"❌ Error: Annotations directory not found at: {annotations_dir}")
        print(f"   Looking for dataset at: {DATASET_PATH}")
        sys.exit(1)

    results = []
    total_annotations = 0
    skipped_missing = 0

    # Process each action's JSON file
    json_files = sorted([f for f in os.listdir(annotations_dir) if f.endswith('.json')])
    print(f"Found {len(json_files)} annotation files: {json_files}")

    for json_file in json_files:
        action_name = json_file.replace('.json', '')
        print(f"\nProcessing action: {action_name}")

        with open(os.path.join(annotations_dir, json_file), 'r') as f:
            data = json.load(f)

        # Build a lookup from image_id -> image info
        image_lookup = {img['id']: img for img in data['images']}

        action_count = 0
        action_skipped = 0

        for annotation in data['annotations']:
            total_annotations += 1
            image_id = annotation['image_id']
            keypoints = annotation['keypoints']
            image_info = image_lookup.get(image_id)

            if image_info is None:
                continue

            # Compute metrics (returns None if keypoints are missing)
            metrics = compute_metrics(keypoints)

            if metrics is None:
                action_skipped += 1
                skipped_missing += 1
                continue

            # Run the risk engine on the computed metrics
            risk = RiskEngine.evaluate_metrics(metrics)

            results.append({
                'action': action_name,
                'image_id': image_id,
                'filename': image_info.get('file_name', ''),
                'left_elbow_angle': round(metrics['left_elbow_angle'], 2),
                'right_elbow_angle': round(metrics['right_elbow_angle'], 2),
                'left_knee_angle': round(metrics['left_knee_angle'], 2),
                'right_knee_angle': round(metrics['right_knee_angle'], 2),
                'left_shoulder_angle': round(metrics['left_shoulder_angle'], 2),
                'right_shoulder_angle': round(metrics['right_shoulder_angle'], 2),
                'hip_angle': round(metrics['hip_angle'], 2),
                'risk_score': risk['risk_score'],
                'risk_level': risk['risk_level'],
                'risk_factors': '; '.join(
                    [f"{f['title']} ({f['detail'][:80]}...)" for f in risk['risk_factors']]
                ) if risk['risk_factors'] else 'None',
            })
            action_count += 1

        print(f"   Processed: {action_count} images | Skipped (missing keypoints): {action_skipped}")

    # Save results to CSV
    output_path = os.path.join(SCRIPT_DIR, 'tennis_dataset_analysis.csv')
    fieldnames = [
        'action', 'image_id', 'filename',
        'left_elbow_angle', 'right_elbow_angle',
        'left_knee_angle', 'right_knee_angle',
        'left_shoulder_angle', 'right_shoulder_angle',
        'hip_angle',
        'risk_score', 'risk_level', 'risk_factors'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Print summary statistics
    print(f"\n{'='*60}")
    print(f"✅ Processing complete!")
    print(f"   Total annotations in dataset: {total_annotations}")
    print(f"   Successfully processed: {len(results)}")
    print(f"   Skipped (missing keypoints): {skipped_missing}")
    print(f"   Results saved to: {output_path}")
    print(f"{'='*60}")

    # Print per-action summary
    from collections import Counter
    action_counts = Counter(r['action'] for r in results)
    print(f"\nPer-action breakdown:")
    for action in sorted(action_counts.keys()):
        action_results = [r for r in results if r['action'] == action]
        avg_risk = np.mean([r['risk_score'] for r in action_results])
        high_count = sum(1 for r in action_results if r['risk_level'] == 'High')
        mod_count = sum(1 for r in action_results if r['risk_level'] == 'Moderate')
        low_count = sum(1 for r in action_results if r['risk_level'] == 'Low')
        print(f"   {action}:")
        print(f"      Images: {action_counts[action]}")
        print(f"      Avg Risk Score: {avg_risk:.1f}")
        print(f"      Risk Distribution: High={high_count}, Moderate={mod_count}, Low={low_count}")


if __name__ == '__main__':
    main()

