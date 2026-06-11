from pathlib import Path
from typing import Any

import pandas as pd


def _safe_value(value: Any):
    """
    Convert pandas/numpy values into JSON-safe Python values.
    """
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def parse_mzmine_quant_csv(file_path: str | Path, ion_mode: str) -> list[dict]:
    """
    Parse MZmine/GNPS quant CSV file.

    Important columns in your file:
    - row ID
    - row m/z
    - row retention time
    - columns ending with 'Peak area'
    """

    file_path = Path(file_path)
    df = pd.read_csv(file_path)

    # Remove useless unnamed columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    required_columns = ["row ID", "row m/z", "row retention time"]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing required column: {column}")

    peak_area_columns = [
        column for column in df.columns
        if column.endswith("Peak area")
    ]

    features = []

    for _, row in df.iterrows():
        row_data = {
            column: _safe_value(row[column])
            for column in df.columns
        }

        peak_areas = {
            column: _safe_value(row[column])
            for column in peak_area_columns
        }

        feature = {
            "feature_id": str(int(row["row ID"])),
            "mz": float(row["row m/z"]),
            "retention_time_minutes": float(row["row retention time"]),
            "ion_mode": ion_mode.upper(),
            "peak_areas": peak_areas,
            "best_ion": _safe_value(row.get("best ion")),
            "neutral_mass": (
                float(row["neutral M mass"])
                if "neutral M mass" in df.columns and pd.notna(row["neutral M mass"])
                else None
            ),
            "raw_row": row_data,
        }

        features.append(feature)

    return features