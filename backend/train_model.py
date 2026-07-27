"""
train_model.py

Trains a Random Forest classifier on the processed tennis dataset
to predict risk level (Low/Moderate/High) from joint angles.

This ML model can augment or replace the rule-based RiskEngine.

Usage:
    cd backend
    source venv/bin/activate
    pip install pandas scikit-learn joblib
    python train_model.py

Output: risk_model.pkl (saved model) + printed evaluation metrics
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, 'tennis_dataset_analysis.csv')
MODEL_OUTPUT = os.path.join(SCRIPT_DIR, 'risk_model.pkl')


def main():
    # --- Load the dataset ---
    print("Loading dataset...")
    df = pd.read_csv(CSV_PATH)
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")

    # --- Prepare features ---
    # We have 7 angle columns (left & right for elbow, knee, shoulder, plus hip)
    feature_columns = [
        'left_elbow_angle', 'right_elbow_angle',
        'left_knee_angle', 'right_knee_angle',
        'left_shoulder_angle', 'right_shoulder_angle',
        'hip_angle',
    ]

    X = df[feature_columns].values

    # --- Encode target labels ---
    # risk_level: Low, Moderate, High
    le = LabelEncoder()
    y = le.fit_transform(df['risk_level'].values)
    print(f"\n  Classes: {le.classes_} -> {list(le.transform(le.classes_))}")
    print(f"  Class distribution:")
    for cls_name, cls_idx in zip(le.classes_, le.transform(le.classes_)):
        count = sum(y == cls_idx)
        print(f"    {cls_name} ({cls_idx}): {count} samples ({count/len(y)*100:.1f}%)")

    # --- Train/test split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  Train size: {len(X_train)}, Test size: {len(X_test)}")

    # --- Train Random Forest ---
    print("\nTraining Random Forest classifier...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=4,
        random_state=42,
        class_weight='balanced',  # handle class imbalance
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # --- Cross-validation ---
    cv_scores = cross_val_score(clf, X_train, y_train, cv=5)
    print(f"\n  5-fold CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # --- Evaluate on test set ---
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n  Test accuracy: {accuracy:.3f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    print(f"\n  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    cm_df = pd.DataFrame(cm, index=le.classes_, columns=le.classes_)
    print(cm_df)

    # --- Feature importance ---
    print("\n  Feature Importances:")
    importances = clf.feature_importances_
    indices = np.argsort(importances)[::-1]
    for i in indices:
        print(f"    {feature_columns[i]}: {importances[i]:.3f}")

    # --- Save model ---
    model_data = {
        'model': clf,
        'label_encoder': le,
        'feature_columns': feature_columns,
        'accuracy': accuracy,
        'cv_mean': cv_scores.mean(),
    }
    joblib.dump(model_data, MODEL_OUTPUT)
    print(f"\n✅ Model saved to: {MODEL_OUTPUT}")


if __name__ == '__main__':
    main()


