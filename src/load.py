
import json
import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.config import get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def load_raw_snapshot(engine, raw_file):
    """Load the specific raw JSON snapshot into PostgreSQL."""

    raw_file = Path(raw_file)

    if not raw_file.exists():
        raise FileNotFoundError(
            f"Raw JSON file not found: {raw_file}"
        )

    with raw_file.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO raw_weather (payload)
                VALUES (CAST(:payload AS JSONB))
            """),
            {"payload": json.dumps(payload)},
        )

    logging.info("Loaded raw snapshot: %s", raw_file.name)


def load_daily_weather(engine, processed_file):
    """Upsert the specific processed CSV into PostgreSQL."""

    processed_file = Path(processed_file)

    if not processed_file.exists():
        raise FileNotFoundError(
            f"Processed CSV not found: {processed_file}"
        )

    df = pd.read_csv(processed_file)

    required = {
        "forecast_date",
        "temp_max_c",
        "temp_min_c",
        "precipitation_mm",
        "ingested_at_utc",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"CSV missing required columns: {missing}"
        )

    records = df.astype(object).where(
        pd.notna(df), None
    ).to_dict(orient="records")

    upsert_sql = text("""
        INSERT INTO daily_weather (
            forecast_date,
            temp_max_c,
            temp_min_c,
            precipitation_mm,
            ingested_at_utc
        )
        VALUES (
            :forecast_date,
            :temp_max_c,
            :temp_min_c,
            :precipitation_mm,
            :ingested_at_utc
        )
        ON CONFLICT (forecast_date)
        DO UPDATE SET
            temp_max_c = EXCLUDED.temp_max_c,
            temp_min_c = EXCLUDED.temp_min_c,
            precipitation_mm = EXCLUDED.precipitation_mm,
            ingested_at_utc = EXCLUDED.ingested_at_utc
    """)

    with engine.begin() as connection:
        connection.execute(upsert_sql, records)

    logging.info(
        "Upserted %s daily forecast records",
        len(records),
    )


def main():
    if len(sys.argv) != 3:
        raise ValueError(
            "Usage: python -m src.load <raw_json_path> "
            "<processed_csv_path>"
        )

    raw_file = sys.argv[1]
    processed_file = sys.argv[2]

    engine = get_engine()

    try:
        load_raw_snapshot(engine, raw_file)
        load_daily_weather(engine, processed_file)
        logging.info("Database load completed successfully")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
