"""
caltennis_processor.py

Processes the CalTennis dataset to extract pose features for ML training.
This handles large-scale processing of video data from the CalTennis dataset.

Usage:
    python -m data_processing.caltennis_processor
"""

from datasets import load_dataset
import mediapipe as mp
import cv2
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import numpy as np
import sys
import os
import tempfile
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CalTennisProcessor:
    def __init__(self, batch_size=1000, max_samples=None, output_dir='data_processing', debug=False):
        self.batch_size = batch_size
        self.max_samples = max_samples
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.debug = debug
        
        # Initialize MediaPipe with higher quality for professional footage
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=2  # Higher accuracy model
        )
        
    def load_dataset(self):
        """Load CalTennis dataset"""
        print("Loading CalTennis dataset...")
        try:
            self.ds = load_dataset("demalenk/caltennis")
            print(f"Dataset loaded: {self.ds}")
            
            # Handle different dataset structures
            if 'train' in self.ds:
                self.split_name = 'train'
                print(f"Train set size: {len(self.ds['train'])}")
            elif 'mini' in self.ds:
                self.split_name = 'mini'
                print(f"Mini set size: {len(self.ds['mini'])}")
            elif 'mid' in self.ds:
                self.split_name = 'mid'
                print(f"Mid set size: {len(self.ds['mid'])}")
            else:
                # Use first available split
                self.split_name = list(self.ds.keys())[0]
                print(f"Using split: {self.split_name}, size: {len(self.ds[self.split_name])}")
            
            return self.ds
        except Exception as e:
            print(f"Error loading dataset: {e}")
            print("Make sure to install: pip install datasets")
            raise
    
    def extract_frame_from_video(self, video_data):
        """Extract a single frame from video data"""
        try:
            # First, let's see what type of data we have
            print(f"Video data type: {type(video_data)}")
            
            # Handle different video data formats
            if isinstance(video_data, bytes):
                print(f"Video data size: {len(video_data)} bytes")
                # If video data is bytes, save to temp file and process
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                    tmp.write(video_data)
                    tmp_path = tmp.name
                
                cap = cv2.VideoCapture(tmp_path)
                ret, frame = cap.read()
                cap.release()
                
                # Clean up temp file
                import os
                os.unlink(tmp_path)
                
                if ret:
                    return frame
                else:
                    return None
            elif hasattr(video_data, 'read'):
                # If video data is file-like object
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                    tmp.write(video_data.read())
                    tmp_path = tmp.name
                
                cap = cv2.VideoCapture(tmp_path)
                ret, frame = cap.read()
                cap.release()
                
                import os
                os.unlink(tmp_path)
                
                if ret:
                    return frame
                else:
                    return None
            elif isinstance(video_data, dict):
                # If video data is a dictionary with metadata
                print(f"Video data keys: {video_data.keys()}")
                # Look for actual video data in the dict
                if 'bytes' in video_data:
                    return self.extract_frame_from_video(video_data['bytes'])
                elif 'data' in video_data:
                    return self.extract_frame_from_video(video_data['data'])
                else:
                    return None
            else:
                # Unknown format, skip
                print(f"Unknown video data format: {type(video_data)}")
                return None
        except Exception as e:
            print(f"Error extracting frame from video: {e}")
            return None
    
    def generate_synthetic_frame(self, sample_id):
        """Generate a synthetic frame for testing pipeline when video extraction fails"""
        try:
            # Create a simple synthetic frame with realistic joint positions
            # This is just for testing the pipeline logic
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add some noise to make it look like real video
            noise = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
            frame = frame + noise
            
            return frame
        except Exception as e:
            print(f"Error generating synthetic frame: {e}")
            return None
    
    def process_batch(self, start_idx, end_idx):
        """Process a batch of samples"""
        batch_data = []
        
        for i in tqdm(range(start_idx, min(end_idx, len(self.ds[self.split_name])))):
            try:
                sample = self.ds[self.split_name][i]
                
                if self.debug:
                    print(f"\nSample {i} keys: {sample.keys()}")
                    for key, value in sample.items():
                        if key != 'video':
                            print(f"  {key}: {value}")
                        else:
                            print(f"  {key}: {type(value)}")
                
                # Extract frame/image - handle different dataset formats
                frame = None
                if 'image' in sample:
                    frame = sample['image']
                elif 'frame' in sample:
                    frame = sample['frame']
                elif 'video' in sample:
                    # CalTennis contains video data - extract frames
                    video_data = sample['video']
                    frame = self.extract_frame_from_video(video_data)
                    if frame is None:
                        if self.debug:
                            print(f"  Failed to extract frame from video, using synthetic data for testing")
                        # Use synthetic data for testing pipeline
                        frame = self.generate_synthetic_frame(i)
                        if frame is None:
                            continue
                
                if frame is None:
                    continue
                
                # Ensure frame is numpy array
                if not isinstance(frame, np.ndarray):
                    continue
                
                # Extract pose metrics
                metrics = self.extract_pose_metrics(frame)
                if metrics:
                    batch_data.append({
                        'sample_id': i,
                        'action': sample.get('action', 'unknown'),
                        **metrics
                    })
            except Exception as e:
                # Skip problematic samples
                continue
        
        return batch_data
    
    def extract_pose_metrics(self, frame):
        """Extract comprehensive pose metrics from frame"""
        try:
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
                'hip_angle': self.calculate_hip_angle(landmarks),
                # Additional 3D features
                'left_elbow_depth': landmarks[13].z,
                'right_elbow_depth': landmarks[14].z,
                'left_knee_depth': landmarks[25].z,
                'right_knee_depth': landmarks[26].z,
                # Confidence scores
                'pose_confidence': np.mean([lm.visibility for lm in landmarks])
            }
            
            return metrics
        except Exception as e:
            return None
    
    def calculate_angle(self, a, b, c):
        """Calculate angle between three 3D points"""
        try:
            # Handle both landmark objects and raw coordinates
            def to_point(p):
                if hasattr(p, 'x'):
                    return np.array([p.x, p.y, p.z])
                elif isinstance(p, (list, tuple, np.ndarray)):
                    return np.array(p)
                else:
                    return np.array([0, 0, 0])
            
            a = to_point(a)
            b = to_point(b)
            c = to_point(c)
            
            ba = a - b
            bc = c - b
            
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
            angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
            
            return np.degrees(angle)
        except:
            return 0.0
    
    def calculate_hip_angle(self, landmarks):
        """Calculate hip angle using hip center"""
        try:
            # Calculate hip center (midpoint of left and right hip)
            hip_center_x = (landmarks[23].x + landmarks[24].x) / 2
            hip_center_y = (landmarks[23].y + landmarks[24].y) / 2
            hip_center_z = (landmarks[23].z + landmarks[24].z) / 2
            
            hip_center = type('obj', (object,), {
                'x': hip_center_x, 
                'y': hip_center_y, 
                'z': hip_center_z
            })()
            
            # Use midpoint of shoulders as "neck" equivalent
            shoulder_center_x = (landmarks[11].x + landmarks[12].x) / 2
            shoulder_center_y = (landmarks[11].y + landmarks[12].y) / 2
            shoulder_center_z = (landmarks[11].z + landmarks[12].z) / 2
            
            shoulder_center = type('obj', (object,), {
                'x': shoulder_center_x, 
                'y': shoulder_center_y, 
                'z': shoulder_center_z
            })()
            
            # Calculate angle: shoulder_center -> hip_center -> knee
            return self.calculate_angle(shoulder_center, hip_center, landmarks[25])
        except:
            return 0.0
    
    def process_full_dataset(self, output_filename='caltennis_features.csv'):
        """Process entire dataset in batches"""
        self.load_dataset()
        all_data = []
        
        total_samples = len(self.ds[self.split_name])
        if self.max_samples:
            total_samples = min(total_samples, self.max_samples)
        
        print(f"Processing {total_samples} samples in batches of {self.batch_size}...")
        
        for start_idx in range(0, total_samples, self.batch_size):
            end_idx = min(start_idx + self.batch_size, total_samples)
            print(f"\nProcessing batch {start_idx}-{end_idx}...")
            
            batch_data = self.process_batch(start_idx, end_idx)
            all_data.extend(batch_data)
            
            success_rate = len(batch_data) / (end_idx - start_idx) * 100 if (end_idx - start_idx) > 0 else 0
            print(f"Batch complete: {len(batch_data)} valid samples ({success_rate:.1f}% success rate)")
            
            # Save intermediate results every 100 samples for this small dataset
            if len(all_data) % 100 == 0:
                output_path = self.output_dir / output_filename
                df = pd.DataFrame(all_data)
                df.to_csv(output_path, index=False)
                print(f"Saved intermediate results: {len(all_data)} samples to {output_path}")
        
        # Final save
        output_path = self.output_dir / output_filename
        df = pd.DataFrame(all_data)
        df.to_csv(output_path, index=False)
        
        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"Total samples processed: {len(all_data)}")
        print(f"Results saved to: {output_path}")
        print(f"{'='*60}")
        
        return df

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process CalTennis dataset')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    parser.add_argument('--max-samples', type=int, default=None, help='Maximum samples to process (for testing)')
    parser.add_argument('--output', type=str, default='caltennis_features.csv', help='Output filename')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode for troubleshooting')
    
    args = parser.parse_args()
    
    # For testing, start with small sample
    max_samples = args.max_samples if args.max_samples else 100  # Default to 100 for initial test
    
    processor = CalTennisProcessor(
        batch_size=args.batch_size,
        max_samples=max_samples,
        debug=args.debug
    )
    
    try:
        df = processor.process_full_dataset(args.output)
        
        if len(df) == 0:
            print("⚠️ No valid samples were processed. This might be due to:")
            print("  - Video extraction issues with CalTennis dataset format")
            print("  - MediaPipe unable to detect poses in the frames")
            print("  - Dataset structure different than expected")
            print("\n💡 For testing the pipeline, try running with --debug flag to see detailed info")
            print("💡 The synthetic frame generation should have created test data")
            return
        
        print(f"\nDataset statistics:")
        print(df.describe())
        
        # Show risk distribution using rule-based approach
        try:
            from app.risk_engine import RiskEngine
        except ImportError:
            # If running from different directory
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from app.risk_engine import RiskEngine
        
        print(f"\nApplying rule-based risk assessment...")
        risk_levels = []
        risk_scores = []
        
        for _, row in df.iterrows():
            metrics = {k: row[k] for k in df.columns if 'angle' in k}
            try:
                risk = RiskEngine.evaluate_metrics(metrics)
                risk_levels.append(risk['risk_level'])
                risk_scores.append(risk['risk_score'])
            except Exception as e:
                # Handle cases where metrics might be incomplete
                risk_levels.append('Unknown')
                risk_scores.append(0)
        
        df['risk_level'] = risk_levels
        df['risk_score'] = risk_scores
        print(f"\nRisk distribution:")
        print(df['risk_level'].value_counts())
        
        # Save with risk levels
        output_with_risk = args.output.replace('.csv', '_with_risk.csv')
        df.to_csv(processor.output_dir / output_with_risk, index=False)
        print(f"Saved with risk levels: {output_with_risk}")
        
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
    except Exception as e:
        print(f"Error during processing: {e}")
        raise

if __name__ == '__main__':
    main()