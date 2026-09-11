"""Shared feature definitions and validation limits."""

DISTRICTS = [
    "Centre-ville",
    "Hay Nahda",
    "Hay Salam",
    "Lotissement El Massira",
    "Hay Moulouya",
    "Hay Bouhdila",
    "Hay Sidi Ahmed",
    "Hay Trifa",
    "Hay Dallas",
    "Hay El Qods",
]

PROPERTY_TYPES = ["apartment", "house", "villa"]
CONDITIONS = ["to_renovate", "good", "renovated", "new"]
BINARY_FEATURES = ["balcony", "garden", "garage", "air_conditioning"]
NUMERIC_FEATURES = [
    "area_m2",
    "bedrooms",
    "bathrooms",
    "floor",
    "age_years",
    *BINARY_FEATURES,
]
CATEGORICAL_FEATURES = ["district", "property_type", "condition"]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET_COLUMN = "price_mad"

RANGES = {
    "area_m2": (20, 1000),
    "bedrooms": (1, 12),
    "bathrooms": (1, 8),
    "floor": (0, 20),
    "age_years": (0, 100),
}

MODEL_VERSION = "1.0"

