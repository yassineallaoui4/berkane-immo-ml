from pathlib import Path
import tempfile
import unittest

from app import create_app
from ml.modeling import train_model
from scripts.generate_demo_data import generate
from tests.test_modeling import VALID_PROPERTY


class ApiTests(unittest.TestCase):
    def test_untrained_api_reports_model_not_ready(self):
        app = create_app("missing-model.joblib")
        response = app.test_client().post("/api/predict", json=VALID_PROPERTY)
        self.assertEqual(response.status_code, 503)

    def test_prediction_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "demo.csv"
            model_path = root / "model.joblib"
            generate(80, 11).to_csv(data_path, index=False)
            train_model(data_path, model_path, root / "metrics.json", data_kind="synthetic-demo")
            app = create_app(model_path)
            response = app.test_client().post("/api/predict", json=VALID_PROPERTY)
            self.assertEqual(response.status_code, 200)
            self.assertIn("estimated_price_mad", response.get_json())


if __name__ == "__main__":
    unittest.main()

