"""Training and inference for the Berkane property-price estimator."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .config import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    CONDITIONS,
    DISTRICTS,
    FEATURE_COLUMNS,
    MODEL_VERSION,
    NUMERIC_FEATURES,
    PROPERTY_TYPES,
    RANGES,
    TARGET_COLUMN,
)


class ModelNotReadyError(RuntimeError):
    """Raised when inference is requested before a model is trained."""


def _coerce_binary(value: Any, field: str) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in (0, 1):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"yes", "true", "1", "oui"}:
            return 1
        if normalized in {"no", "false", "0", "non"}:
            return 0
    raise ValueError(f"{field} must be yes/no or 1/0")


def validate_property(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one property record."""
    if not isinstance(payload, dict):
        raise ValueError("The request body must be a JSON object")

    missing = [field for field in FEATURE_COLUMNS if field not in payload]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    district = str(payload["district"]).strip()
    property_type = str(payload["property_type"]).strip().lower()
    condition = str(payload["condition"]).strip().lower()

    if district not in DISTRICTS:
        raise ValueError("district is not supported")
    if property_type not in PROPERTY_TYPES:
        raise ValueError("property_type is not supported")
    if condition not in CONDITIONS:
        raise ValueError("condition is not supported")

    normalized: dict[str, Any] = {
        "district": district,
        "property_type": property_type,
        "condition": condition,
    }

    for field, (minimum, maximum) in RANGES.items():
        try:
            value = float(payload[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} must be numeric") from exc
        if not minimum <= value <= maximum:
            raise ValueError(f"{field} must be between {minimum} and {maximum}")
        normalized[field] = value

    for field in BINARY_FEATURES:
        normalized[field] = _coerce_binary(payload[field], field)

    return normalized


def build_pipeline() -> Pipeline:
    """Create the preprocessing and Random Forest regression pipeline."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
    regressor = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])


def _validate_training_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = FEATURE_COLUMNS + [TARGET_COLUMN]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Training data is missing columns: {', '.join(missing)}")
    if len(frame) < 30:
        raise ValueError("Training requires at least 30 rows")

    clean = frame[required].dropna().copy()
    if len(clean) < 30:
        raise ValueError("Training requires at least 30 complete rows")
    if (clean[TARGET_COLUMN] <= 0).any():
        raise ValueError("price_mad must contain positive values")

    for field in BINARY_FEATURES:
        clean[field] = clean[field].map(lambda value: _coerce_binary(value, field))
    for field in NUMERIC_FEATURES:
        clean[field] = pd.to_numeric(clean[field], errors="raise")
    clean[TARGET_COLUMN] = pd.to_numeric(clean[TARGET_COLUMN], errors="raise")
    return clean


def train_model(
    data_path: str | Path,
    model_path: str | Path,
    metrics_path: str | Path,
    *,
    data_kind: str = "real",
) -> dict[str, Any]:
    """Train, evaluate, and save a model bundle and metrics file."""
    frame = _validate_training_frame(pd.read_csv(data_path))
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURE_COLUMNS],
        frame[TARGET_COLUMN],
        test_size=0.2,
        random_state=42,
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    mae = float(mean_absolute_error(y_test, predictions))
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    r2 = float(r2_score(y_test, predictions))
    trained_at = datetime.now(timezone.utc).isoformat()

    metadata = {
        "model_version": MODEL_VERSION,
        "algorithm": "RandomForestRegressor",
        "data_kind": data_kind,
        "rows": int(len(frame)),
        "test_rows": int(len(y_test)),
        "mae_mad": round(mae, 2),
        "rmse_mad": round(rmse, 2),
        "r2": round(r2, 4),
        "trained_at": trained_at,
        "features": FEATURE_COLUMNS,
    }

    model_file = Path(model_path)
    metrics_file = Path(metrics_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metadata": metadata}, model_file)
    metrics_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_model(model_path: str | Path) -> dict[str, Any]:
    model_file = Path(model_path)
    if not model_file.exists():
        raise ModelNotReadyError(
            "No trained model was found. Run the training command from the README first."
        )
    bundle = joblib.load(model_file)
    if not isinstance(bundle, dict) or "pipeline" not in bundle or "metadata" not in bundle:
        raise ModelNotReadyError("The saved model bundle is invalid")
    return bundle


def predict_property(payload: dict[str, Any], model_path: str | Path) -> dict[str, Any]:
    """Predict one price and provide an uncertainty band based on validation MAE."""
    normalized = validate_property(payload)
    bundle = load_model(model_path)
    frame = pd.DataFrame([normalized], columns=FEATURE_COLUMNS)
    estimate = max(0.0, float(bundle["pipeline"].predict(frame)[0]))
    mae = float(bundle["metadata"].get("mae_mad", 0.0))
    return {
        "estimated_price_mad": round(estimate),
        "lower_bound_mad": round(max(0.0, estimate - mae)),
        "upper_bound_mad": round(estimate + mae),
        "model": bundle["metadata"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the Berkane price model")
    parser.add_argument("--data", required=True, help="Input CSV")
    parser.add_argument("--model", default="models/berkane_price_model.joblib")
    parser.add_argument("--metrics", default="models/metrics.json")
    parser.add_argument(
        "--data-kind",
        choices=["real", "synthetic-demo"],
        default="real",
        help="Recorded in model metadata to prevent misleading claims",
    )
    args = parser.parse_args()
    metrics = train_model(
        args.data,
        args.model,
        args.metrics,
        data_kind=args.data_kind,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

