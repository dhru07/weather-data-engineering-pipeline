
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

REQUIRED_FIELDS = [
    "time",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def transform_weather_data(data):
    """Convert raw API arrays into validated, row-based records."""

    daily = data.get("daily")

    if not isinstance(daily, dict):
        raise ValueError("Missing or invalid daily section")

    missing_fields = [
        field for field in REQUIRED_FIELDS
        if field not in daily
    ]

    if missing_fields:
        raise ValueError(f"Missing fields: {missing_fields}")

    dates = daily["time"]

    if not isinstance(dates, list) or not dates:
        raise ValueError("No forecast dates found")

    for field in REQUIRED_FIELDS[1:]:
        if not isinstance(daily[field], list):
            raise ValueError(f"{field} must be a list")

        if len(daily[field]) != len(dates):
            raise ValueError(
                f"{field} length does not match time length"
            )

    df = pd.DataFrame({
        "forecast_date": dates,
        "temp_max_c": daily["temperature_2m_max"],
        "temp_min_c": daily["temperature_2m_min"],
        "precipitation_mm": daily["precipitation_sum"],
    })

    df["forecast_date"] = pd.to_datetime(
        df["forecast_date"], errors="raise"
    ).dt.date

    if df["forecast_date"].duplicated().any():
        raise ValueError("Duplicate forecast dates found")

    metric_columns = [
        "temp_max_c",
        "temp_min_c",
        "precipitation_mm",
    ]

    for column in metric_columns:
        df[column] = pd.to_numeric(
            df[column], errors="raise"
        )

    if (df["precipitation_mm"].dropna() < 0).any():
        raise ValueError("Negative precipitation found")

    valid_temps = (
        df["temp_max_c"].notna()
        & df["temp_min_c"].notna()
    )

    if (
        df.loc[valid_temps, "temp_max_c"]
        < df.loc[valid_temps, "temp_min_c"]
    ).any():
        raise ValueError("Maximum temperature below minimum")

    df["ingested_at_utc"] = datetime.now(
        timezone.utc
    ).isoformat()

    logging.info("Transformed %s forecast records", len(df))

    return df


def transform_file(raw_file):
    """Transform one specific raw JSON file into a CSV file."""

    raw_file = Path(raw_file)

    if not raw_file.exists():
        raise FileNotFoundError(
            f"Raw JSON file not found: {raw_file}"
        )

    with raw_file.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    df = transform_weather_data(raw_data)

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = PROCESSED_DATA_DIR / (
        f"{raw_file.stem}_processed.csv"
    )

    df.to_csv(output_file, index=False)

    logging.info("Transformed file saved to %s", output_file)

    return output_file


def main():
    if len(sys.argv) != 2:
        raise ValueError(
            "Usage: python -m src.transform <raw_json_path>"
        )

    output_file = transform_file(sys.argv[1])

    # Final stdout line is captured by Airflow XCom.
    print(output_file)


if __name__ == "__main__":
    main()
