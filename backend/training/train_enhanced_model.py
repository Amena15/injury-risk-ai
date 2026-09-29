import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def train_enhanced_model(csv_path='data_processing/enhanced_tennis_dataset.csv'):
    """
    Train ensemble model on enhanced features
    """
    print("🚀 Loading enhanced dataset...")
    
    # Try multiple possible CSV locations
    possible_paths = [
        csv_path,
        'data_processing/enhanced_tennis_dataset.csv',
        'tennis_dataset_analysis.csv',
        '../tennis_dataset_analysis.csv'
    ]
    
    df = None
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✓ Found dataset at: {path}")
            df = pd.read_csv(path)
            break
    
    if df is None:
        print("❌ Error: No dataset found. Please run enhanced_dataset_processor.py first.")
        return None, None
    
    # Identify feature columns (exclude non-feature columns)
    exclude_cols = ['sample_id', 'risk_label', 'video_path', 'filename', 'action', 'image_id', 'risk_factors', 'risk_score']
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    # Debug: Print excluded columns to verify
    print(f"🔍 Excluding columns: {exclude_cols}")
    print(f"🔍 Available columns: {df.columns.tolist()}")
    print(f"🔍 Selected features: {feature_cols}")
    
    # Double-check risk_score is not in features
    if 'risk_score' in feature_cols:
        print("❌ ERROR: risk_score is still in features! Removing it manually.")
        feature_cols = [col for col in feature_cols if col != 'risk_score']
    
    # Check if we have a risk_level column
    if 'risk_level' not in df.columns:
        print("❌ Error: No 'risk_level' column found in dataset.")
        print(f"Available columns: {df.columns.tolist()}")
        return None, None
    
    X = df[feature_cols]
    y = df['risk_level']
    
    # Handle missing values
    X = X.fillna(X.mean())
    
    print(f"📊 Dataset shape: {X.shape}")
    print(f" Number of features: {len(feature_cols)}")
    print(f"🎯 Class distribution:\n{y.value_counts()}")
    
    # Create Ensemble Model
    print("\n🤖 Initializing Ensemble Model...")
    models = [
        ('rf', RandomForestClassifier(
            n_estimators=200, 
            max_depth=10, 
            class_weight='balanced', 
            random_state=42,
            n_jobs=-1
        )),
        ('gb', GradientBoostingClassifier(
            n_estimators=100, 
            max_depth=5, 
            random_state=42
        ))
    ]
    
    ensemble = VotingClassifier(
        estimators=models, 
        voting='soft', 
        weights=[2, 1]
    )
    
    # Cross-Validation
    print("\n🔄 Running 5-Fold Cross-Validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('ensemble', ensemble),
    ])
    cv_scores = cross_val_score(cv_pipeline, X, y, cv=cv, scoring='f1_weighted')
    print(f"✅ CV F1 Score: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    
    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"\n📚 Training on {len(X_train)} samples...")
    ensemble.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = ensemble.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n" + "="*60)
    print("📊 TEST SET PERFORMANCE")
    print("="*60)
    print(f"Accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature Importance (from Random Forest)
    rf_model = ensemble.named_estimators_['rf']
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n" + "="*60)
    print("🏆 TOP 10 MOST IMPORTANT FEATURES")
    print("="*60)
    print(feature_importance.head(10).to_string(index=False))
    
    # Save model
    os.makedirs('models', exist_ok=True)
    model_path = 'models/enhanced_risk_model.pkl'
    joblib.dump({
        'model': ensemble, 
        'scaler': scaler, 
        'features': feature_cols,
        'accuracy': accuracy,
        'cv_score': cv_scores.mean()
    }, model_path)
    
    print(f"\n💾 Model saved to: {model_path}")
    print(f"📦 Model size: {os.path.getsize(model_path) / 1024:.1f} KB")
    
    return ensemble, feature_cols

if __name__ == "__main__":
    train_enhanced_model()