
import logging

from src.ingest import fetch_weather_data, save_raw_data
from src.transform import transform_weather_data
from src.config import PROJECT_ROOT, get_engine
from src.load import load_raw_snapshot, load_daily_weather

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def run_pipeline():
    engine = None

    try:
        logging.info("=== Weather ETL pipeline started ===")

        # 1. Extract
        data = fetch_weather_data()
        save_raw_data(data)

        # 2. Transform
        df = transform_weather_data(data)

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_file = PROCESSED_DIR / "weather_forecast.csv"
        df.to_csv(output_file, index=False)

        logging.info("Transformed data saved: %s", output_file)

        # 3. Load
        engine = get_engine()
        load_raw_snapshot(engine)
        load_daily_weather(engine)

        logging.info(
            "=== Pipeline completed successfully: %s records ===",
            len(df),
        )

    except Exception:
        logging.exception("Weather ETL pipeline failed")
        raise

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    run_pipeline()
