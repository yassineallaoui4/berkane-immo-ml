"""Generate deterministic synthetic data for a local functionality demo.

The output is artificial and must never be described as Berkane market evidence.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ml.config import CONDITIONS, DISTRICTS, PROPERTY_TYPES

DISTRICT_PRICE = {
    "Centre-ville": 10_800,
    "Hay Nahda": 9_500,
    "Hay Salam": 8_900,
    "Lotissement El Massira": 10_200,
    "Hay Moulouya": 8_500,
    "Hay Bouhdila": 7_900,
    "Hay Sidi Ahmed": 8_200,
    "Hay Trifa": 7_700,
    "Hay Dallas": 8_700,
    "Hay El Qods": 9_300,
}


def generate(rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records = []
    type_factor = {"apartment": 0.93, "house": 1.0, "villa": 1.2}
    condition_factor = {"to_renovate": 0.78, "good": 1.0, "renovated": 1.1, "new": 1.17}

    for _ in range(rows):
        district = str(rng.choice(DISTRICTS))
        property_type = str(rng.choice(PROPERTY_TYPES, p=[0.5, 0.35, 0.15]))
        condition = str(rng.choice(CONDITIONS, p=[0.12, 0.48, 0.2, 0.2]))
        area = int(rng.integers(45, 320))
        bedrooms = int(np.clip(round(area / 42 + rng.normal(0, 0.8)), 1, 8))
        bathrooms = int(np.clip(round(bedrooms / 2.4 + rng.normal(0, 0.5)), 1, 5))
        floor = int(rng.integers(0, 7)) if property_type == "apartment" else 0
        age = int(rng.integers(0, 46))
        balcony = int(rng.random() < 0.62)
        garden = int(rng.random() < (0.65 if property_type != "apartment" else 0.08))
        garage = int(rng.random() < (0.7 if property_type != "apartment" else 0.35))
        air_conditioning = int(rng.random() < 0.55)

        amenity_bonus = 45_000 * balcony + 110_000 * garden + 85_000 * garage + 35_000 * air_conditioning
        room_bonus = 18_000 * bedrooms + 28_000 * bathrooms
        age_factor = max(0.72, 1 - age * 0.006)
        base = area * DISTRICT_PRICE[district] * type_factor[property_type] * condition_factor[condition] * age_factor
        noise = rng.normal(0, max(45_000, base * 0.07))
        price = max(180_000, round(base + amenity_bonus + room_bonus + noise))
        records.append(
            {
                "district": district,
                "property_type": property_type,
                "condition": condition,
                "area_m2": area,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "floor": floor,
                "age_years": age,
                "balcony": balcony,
                "garden": garden,
                "garage": garage,
                "air_conditioning": air_conditioning,
                "price_mad": price,
            }
        )
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic demo properties")
    parser.add_argument("--rows", type=int, default=600)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/demo_properties.csv")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    generate(args.rows, args.seed).to_csv(output, index=False)
    print(f"Wrote {args.rows} synthetic rows to {output}")


if __name__ == "__main__":
    main()

