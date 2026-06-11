import pandas as pd
from pathlib import Path


def parse_mzmine_quant_csv(file_path: str | Path, ion_mode: str) -> list[dict]:
    """
    Parse MZmine/GNPS quant CSV file.

    Expected important columns:
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
        feature = {
            "feature_id": int(row["row ID"]),
            "mz": float(row["row m/z"]),
            "retention_time": float(row["row retention time"]),
            "ion_mode": ion_mode.upper(),
            "peak_areas": {
                column: float(row[column]) if pd.notna(row[column]) else None
                for column in peak_area_columns
            },
            "best_ion": row.get("best ion") if pd.notna(row.get("best ion")) else None,
            "neutral_mass": (
                float(row["neutral M mass"])
                if "neutral M mass" in df.columns and pd.notna(row["neutral M mass"])
                else None
            ),
            "raw_row": row.where(pd.notna(row), None).to_dict(),
        }

        features.append(feature)

    return features