from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
DATASET_PATH = BACKEND_ROOT / "data_processing" / "enhanced_tennis_dataset.csv"
PIPELINE_PATH = BACKEND_ROOT / "models" / "leak_free_risk_pipeline.pkl"


def train_and_plot():
    print(f"Loading dataset: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)

    zscore_cols = [column for column in df.columns if "zscore" in column.lower()]
    df = df.drop(columns=zscore_cols)
    print(f"Dropped {len(zscore_cols)} pre-calculated z-score columns.")

    exclude_cols = {
        "sample_id", "risk_label", "video_path", "filename", "action",
        "image_id", "risk_factors", "risk_score", "risk_level",
    }
    feature_cols = [
        column for column in df.columns
        if column not in exclude_cols and pd.api.types.is_numeric_dtype(df[column])
    ]
    if not feature_cols:
        raise ValueError("No numeric feature columns were found in the dataset.")
    if "risk_level" not in df.columns:
        raise ValueError("Dataset must contain a 'risk_level' target column.")

    X = df[feature_cols]
    y = df["risk_level"]
    print(f"Features ({len(feature_cols)}): {feature_cols}")
    print(f"Classes: {y.value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"Training samples: {len(X_train)}, test samples: {len(X_test)}")

    ensemble = VotingClassifier(
        estimators=[
            ("rf", RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )),
            ("gb", GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42,
            )),
        ],
        voting="soft",
        weights=[2, 1],
    )
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="mean", keep_empty_features=True)),
        ("scaler", StandardScaler()),
        ("model", ensemble),
    ])

    print("\nRunning 5-fold cross-validation on training data...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_weighted")
    print(f"CV weighted F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    print("\nTraining final pipeline...")
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    classes = pipeline.named_steps["model"].classes_

    print("\n" + "=" * 60)
    print(f"FINAL LEAK-FREE HOLDOUT ACCURACY: {accuracy:.3f}")
    print("=" * 60)
    print(classification_report(y_test, y_pred, zero_division=0))

    assets_dir = PROJECT_ROOT / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    matrix = confusion_matrix(y_test, y_pred, labels=classes)
    fig, axis = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=classes,
        yticklabels=classes,
        ax=axis,
    )
    axis.set_title("Confusion Matrix: Biomechanical Risk Classification")
    axis.set_xlabel("Predicted Label")
    axis.set_ylabel("True Label")
    fig.tight_layout()
    fig.savefig(assets_dir / "confusion_matrix.png", dpi=300)
    plt.close(fig)
    print(f"Saved: {assets_dir / 'confusion_matrix.png'}")

    rf_model = pipeline.named_steps["model"].named_estimators_["rf"]
    importances = pd.DataFrame({
        "feature": feature_cols,
        "importance": rf_model.feature_importances_,
    }).sort_values("importance", ascending=False).head(10)

    fig, axis = plt.subplots(figsize=(10, 6))
    sns.barplot(data=importances, x="importance", y="feature", hue="feature", palette="viridis", legend=False, ax=axis)
    axis.set_title("Top 10 Most Important Biomechanical Features")
    axis.set_xlabel("Importance Score")
    axis.set_ylabel("Feature")
    fig.tight_layout()
    fig.savefig(assets_dir / "feature_importance.png", dpi=300)
    plt.close(fig)
    print(f"Saved: {assets_dir / 'feature_importance.png'}")

    PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, PIPELINE_PATH)
    print(f"Saved leak-free pipeline to: {PIPELINE_PATH}")
    return pipeline, accuracy, cv_scores


if __name__ == "__main__":
    train_and_plot()
