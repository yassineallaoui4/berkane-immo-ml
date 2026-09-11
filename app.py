"""Flask API and static-file server for Berkane Immo ML."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from ml.modeling import ModelNotReadyError, load_model, predict_property

ROOT = Path(__file__).resolve().parent
MODEL_PATH = Path(os.environ.get("BERKANE_MODEL_PATH", ROOT / "models" / "berkane_price_model.joblib"))


def create_app(model_path: str | Path | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    active_model_path = Path(model_path) if model_path else MODEL_PATH

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "model_ready": active_model_path.exists()})

    @app.get("/api/model-info")
    def model_info():
        try:
            metadata = load_model(active_model_path)["metadata"]
        except ModelNotReadyError as exc:
            return jsonify({"ready": False, "message": str(exc)}), 503
        return jsonify({"ready": True, "model": metadata})

    @app.post("/api/predict")
    def predict():
        try:
            result = predict_property(request.get_json(silent=True), active_model_path)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except ModelNotReadyError as exc:
            return jsonify({"error": str(exc)}), 503
        return jsonify(result)

    @app.get("/")
    def home():
        return send_from_directory(ROOT, "index.html")

    @app.get("/<path:asset_path>")
    def assets(asset_path: str):
        return send_from_directory(ROOT, asset_path)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

