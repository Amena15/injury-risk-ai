import pandas as pd
import numpy as np
import joblib
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))


def resolve_backend_path(path):
    path = Path(path)
    return path if path.is_absolute() else BACKEND_ROOT / path

def select_samples_for_expert_labeling(
    model_path=None,
    csv_path=None,
    num_samples=50
):
    """
    Select most uncertain samples for expert labeling using entropy
    """
    print("🎯 Selecting most uncertain samples for expert labeling...")
    
    # Load model
    model_path = resolve_backend_path(model_path or 'models/enhanced_risk_model.pkl')
    csv_path = resolve_backend_path(csv_path or 'data_processing/enhanced_tennis_dataset.csv')

    if not model_path.exists():
        print(f"❌ Error: Model not found at {model_path}")
        print("   Please run train_enhanced_model.py first.")
        return
    
    print(f"✓ Loading model from: {model_path}")
    data = joblib.load(model_path)
    model = data['model']
    scaler = data['scaler']
    feature_cols = data['features']
    
    # Load dataset
    possible_paths = [
        csv_path,
        BACKEND_ROOT / 'data_processing' / 'enhanced_tennis_dataset.csv',
        BACKEND_ROOT / 'tennis_dataset_analysis.csv',
    ]
    df = None
    for path in possible_paths:
        if path.exists():
            print(f"✓ Loading dataset from: {path}")
            df = pd.read_csv(path)
            break
    
    if df is None:
        print("❌ Error: Dataset not found.")
        return
    
    # Prepare features
    X = df[feature_cols].fillna(df[feature_cols].mean())
    X_scaled = scaler.transform(X)
    
    # Get probability predictions
    print("\n🔮 Calculating prediction uncertainty...")
    probabilities = model.predict_proba(X_scaled)
    
    # Calculate entropy (uncertainty)
    # High entropy = model is confused
    entropy = -np.sum(probabilities * np.log(probabilities + 1e-10), axis=1)
    
    # Add to dataframe
    df['uncertainty_score'] = entropy
    
    # Sort by uncertainty (highest first)
    df = df.sort_values(by='uncertainty_score', ascending=False)
    
    # Select top N
    selected = df.head(num_samples).copy()
    
    # Save
    label_columns = ['risk_level', 'risk_score', 'risk_factors']
    selected = selected.drop(columns=[column for column in label_columns if column in selected.columns])
    selected['expert_risk_level'] = ''

    output_path = BACKEND_ROOT / 'data_processing' / 'for_expert_labeling.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(output_path, index=False)
    
    print("\n" + "="*60)
    print("✅ SAMPLE SELECTION COMPLETE")
    print("="*60)
    print(f"Selected: {len(selected)} highly uncertain samples")
    print(f"Saved to: {output_path}")
    print(f"Average uncertainty: {selected['uncertainty_score'].mean():.3f}")
    print(f"Uncertainty range: {selected['uncertainty_score'].min():.3f} - {selected['uncertainty_score'].max():.3f}")
    
    # Show top 5 most uncertain
    print("\n📋 TOP 5 MOST UNCERTAIN SAMPLES:")
    for idx, row in selected.head(5).iterrows():
        print(f"  Sample {row.get('image_id', idx)}: uncertainty={row['uncertainty_score']:.3f}")
    
    print("\n� Next Steps:")
    print("  1. Open data_processing/for_expert_labeling.csv")
    print("  2. Have an expert label these samples")
    print("  3. Enter expert judgments in the 'expert_risk_level' column")
    print("  4. Review and merge expert labels before retraining")

if __name__ == "__main__":
    select_samples_for_expert_labeling()