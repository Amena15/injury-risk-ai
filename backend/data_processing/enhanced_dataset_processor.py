"""
enhanced_dataset_processor.py

Enhanced processor for the existing tennis dataset with advanced features.
This demonstrates the scaling concepts from the architecture plan.

Usage:
    python -m data_processing.enhanced_dataset_processor
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EnhancedDatasetProcessor:
    def __init__(self, input_csv='tennis_dataset_analysis.csv', output_dir='data_processing'):
        self.input_csv = input_csv
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_existing_data(self):
        """Load the existing dataset"""
        csv_path = Path(__file__).parent.parent / self.input_csv
        if not csv_path.exists():
            raise FileNotFoundError(f"Dataset not found at {csv_path}")
        
        df = pd.read_csv(csv_path)
        print(f"Loaded existing dataset: {len(df)} samples")
        return df
    
    def extract_advanced_features(self, df):
        """Extract advanced features from existing pose data"""
        print("Extracting advanced features...")
        
        # Make a copy to avoid modifying original
        enhanced_df = df.copy()
        
        # Get angle columns
        angle_cols = [col for col in df.columns if 'angle' in col]
        
        # Statistical features
        for col in angle_cols:
            # Z-score normalization
            mean_val = enhanced_df[col].mean()
            std_val = enhanced_df[col].std()
            enhanced_df[f'{col}_zscore'] = (enhanced_df[col] - mean_val) / (std_val + 1e-8)
            
            # Risk indicators
            enhanced_df[f'{col}_extreme'] = ((enhanced_df[col] < 30) | (enhanced_df[col] > 160)).astype(int)
            
            # Optimal range indicators
            if 'elbow' in col:
                enhanced_df[f'{col}_optimal'] = ((enhanced_df[col] >= 45) & (enhanced_df[col] <= 135)).astype(int)
            elif 'knee' in col:
                enhanced_df[f'{col}_optimal'] = ((enhanced_df[col] >= 20) & (enhanced_df[col] <= 150)).astype(int)
            elif 'shoulder' in col:
                enhanced_df[f'{col}_optimal'] = ((enhanced_df[col] >= 30) & (enhanced_df[col] <= 150)).astype(int)
        
        # Inter-joint coordination metrics
        if 'left_elbow_angle' in enhanced_df.columns and 'left_knee_angle' in enhanced_df.columns:
            enhanced_df['elbow_knee_ratio'] = enhanced_df['left_elbow_angle'] / (enhanced_df['left_knee_angle'] + 1)
        
        if 'right_elbow_angle' in enhanced_df.columns and 'right_knee_angle' in enhanced_df.columns:
            enhanced_df['right_elbow_knee_ratio'] = enhanced_df['right_elbow_angle'] / (enhanced_df['right_knee_angle'] + 1)
        
        # Side symmetry metrics
        if 'left_elbow_angle' in enhanced_df.columns and 'right_elbow_angle' in enhanced_df.columns:
            enhanced_df['elbow_symmetry'] = abs(enhanced_df['left_elbow_angle'] - enhanced_df['right_elbow_angle'])
        
        if 'left_knee_angle' in enhanced_df.columns and 'right_knee_angle' in enhanced_df.columns:
            enhanced_df['knee_symmetry'] = abs(enhanced_df['left_knee_angle'] - enhanced_df['right_knee_angle'])
        
        # Overall movement quality score
        enhanced_df['movement_quality'] = (
            enhanced_df[[col for col in enhanced_df.columns if 'optimal' in col]].sum(axis=1) / 
            len([col for col in enhanced_df.columns if 'optimal' in col])
        )
        
        print(f"Enhanced features: {len(enhanced_df.columns)} columns (was {len(df.columns)})")
        return enhanced_df
    
    def create_data_augmentation(self, df, augmentation_factor=3):
        """Create augmented samples through noise injection"""
        print(f"Creating data augmentation (factor: {augmentation_factor})...")
        
        augmented_samples = []
        angle_cols = [col for col in df.columns if 'angle' in col]
        
        for _, row in tqdm(df.iterrows(), total=len(df)):
            # Original sample
            augmented_samples.append(row.to_dict())
            
            # Create augmented versions
            for i in range(augmentation_factor):
                # Create a fresh copy for each augmentation
                import copy
                augmented_row = copy.deepcopy(row.to_dict())
                
                # Add small random noise to angles
                for col in angle_cols:
                    noise = np.random.normal(0, 2.0)  # 2-degree standard deviation
                    augmented_row[col] = augmented_row[col] + noise
                
                # Recalculate risk score for augmented sample
                try:
                    from app.risk_engine import RiskEngine
                except ImportError:
                    import sys
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from app.risk_engine import RiskEngine
                
                try:
                    metrics = {col: augmented_row[col] for col in angle_cols}
                    risk = RiskEngine.evaluate_metrics(metrics)
                    augmented_row['risk_score'] = risk['risk_score']
                    augmented_row['risk_level'] = risk['risk_level']
                except:
                    pass
                
                augmented_samples.append(augmented_row)
        
        augmented_df = pd.DataFrame(augmented_samples)
        print(f"Augmented dataset: {len(augmented_df)} samples (original: {len(df)})")
        return augmented_df
    
    def analyze_feature_importance(self, df):
        """Analyze which features are most predictive"""
        print("Analyzing feature importance...")
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
        
        # Prepare features
        feature_cols = [col for col in df.columns if col not in ['action', 'image_id', 'filename', 'risk_level', 'risk_score', 'risk_factors']]
        X = df[feature_cols].fillna(0)
        
        # Encode labels
        le = LabelEncoder()
        y = le.fit_transform(df['risk_level'])
        
        # Train quick random forest for feature importance
        rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf.fit(X, y)
        
        # Get feature importance
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Most Important Features:")
        print(importance_df.head(10).to_string(index=False))
        
        return importance_df
    
    def generate_quality_report(self, df):
        """Generate a comprehensive data quality report"""
        print("\n" + "="*60)
        print("DATASET QUALITY REPORT")
        print("="*60)
        
        print(f"\n📊 Basic Statistics:")
        print(f"  Total samples: {len(df)}")
        print(f"  Total features: {len(df.columns)}")
        print(f"  Missing values: {df.isnull().sum().sum()}")
        
        print(f"\n🎯 Risk Distribution:")
        print(df['risk_level'].value_counts())
        print(f"  Risk score distribution:")
        print(f"    Mean: {df['risk_score'].mean():.1f}")
        print(f"    Std: {df['risk_score'].std():.1f}")
        print(f"    Min: {df['risk_score'].min():.1f}")
        print(f"    Max: {df['risk_score'].max():.1f}")
        
        print(f"\n📐 Joint Angle Statistics:")
        angle_cols = [col for col in df.columns if 'angle' in col]
        for col in angle_cols:
            print(f"  {col}:")
            print(f"    Mean: {df[col].mean():.1f}°")
            print(f"    Std: {df[col].std():.1f}°")
            print(f"    Range: {df[col].min():.1f}° - {df[col].max():.1f}°")
        
        print(f"\n🏃 Action Distribution:")
        if 'action' in df.columns:
            print(df['action'].value_counts())
        
        print("="*60)
    
    def save_enhanced_dataset(self, df, filename='enhanced_tennis_dataset.csv'):
        """Save the enhanced dataset"""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        print(f"✅ Enhanced dataset saved to: {output_path}")
        return output_path

def main():
    """Main processing pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhance existing tennis dataset')
    parser.add_argument('--input', type=str, default='tennis_dataset_analysis.csv', help='Input CSV file')
    parser.add_argument('--augment', action='store_true', help='Enable data augmentation')
    parser.add_argument('--augment-factor', type=int, default=3, help='Augmentation factor')
    parser.add_argument('--output', type=str, default='enhanced_tennis_dataset.csv', help='Output filename')
    
    args = parser.parse_args()
    
    processor = EnhancedDatasetProcessor(input_csv=args.input)
    
    try:
        # Load existing data
        df = processor.load_existing_data()
        
        # Extract advanced features
        enhanced_df = processor.extract_advanced_features(df)
        
        # Apply data augmentation if requested
        if args.augment:
            enhanced_df = processor.create_data_augmentation(enhanced_df, args.augment_factor)
        
        # Analyze feature importance
        importance = processor.analyze_feature_importance(enhanced_df)
        
        # Generate quality report
        processor.generate_quality_report(enhanced_df)
        
        # Save enhanced dataset
        processor.save_enhanced_dataset(enhanced_df, args.output)
        
        # Save feature importance
        importance_path = processor.output_dir / 'feature_importance.csv'
        importance.to_csv(importance_path, index=False)
        print(f"✅ Feature importance saved to: {importance_path}")
        
        print(f"\n🎉 Processing complete! Enhanced dataset ready for ML training.")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        raise

if __name__ == '__main__':
    main()