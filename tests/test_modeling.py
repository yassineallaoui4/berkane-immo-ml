from pathlib import Path
import tempfile
import unittest

from ml.modeling import predict_property, train_model, validate_property
from scripts.generate_demo_data import generate


VALID_PROPERTY = {
    "district": "Centre-ville",
    "property_type": "apartment",
    "condition": "good",
    "area_m2": 95,
    "bedrooms": 3,
    "bathrooms": 2,
    "floor": 2,
    "age_years": 8,
    "balcony": True,
    "garden": False,
    "garage": True,
    "air_conditioning": True,
}


class ModelingTests(unittest.TestCase):
    def test_validation_normalizes_binary_fields(self):
        normalized = validate_property(VALID_PROPERTY)
        self.assertEqual(normalized["balcony"], 1)
        self.assertEqual(normalized["garden"], 0)

    def test_validation_rejects_out_of_range_area(self):
        invalid = dict(VALID_PROPERTY, area_m2=5)
        with self.assertRaisesRegex(ValueError, "area_m2"):
            validate_property(invalid)

    def test_training_and_prediction_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "demo.csv"
            model_path = root / "model.joblib"
            metrics_path = root / "metrics.json"
            generate(80, 7).to_csv(data_path, index=False)
            metrics = train_model(
                data_path,
                model_path,
                metrics_path,
                data_kind="synthetic-demo",
            )
            prediction = predict_property(VALID_PROPERTY, model_path)
            self.assertEqual(metrics["data_kind"], "synthetic-demo")
            self.assertGreater(prediction["estimated_price_mad"], 0)
            self.assertLessEqual(prediction["lower_bound_mad"], prediction["upper_bound_mad"])


if __name__ == "__main__":
    unittest.main()

