
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

API_URL = "https://api.open-meteo.com/v1/forecast"

PARAMS = {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "daily": [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
    ],
    "timezone": "Asia/Kolkata",
    "forecast_days": 7,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def fetch_weather_data():
    """Fetch weather data with automatic retries."""

    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(max_retries=retry_strategy),
    )

    try:
        logging.info("Requesting weather data from API")

        response = session.get(
            API_URL,
            params=PARAMS,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict) or "daily" not in data:
            raise ValueError(
                "API response does not contain daily weather data"
            )

        logging.info("Weather data fetched successfully")
        return data

    finally:
        session.close()


def save_raw_data(data):
    """Save the original API response as a unique JSON snapshot."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    file_path = RAW_DATA_DIR / f"weather_{timestamp}.json"

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    logging.info("Raw data saved to %s", file_path)

    return file_path


def main():
    data = fetch_weather_data()
    file_path = save_raw_data(data)

    print("\nAPI response preview:")
    print(json.dumps(data["daily"], indent=2))

    # Keep this as the final stdout line.
    # Airflow BashOperator will capture it through XCom.
    print(file_path)


if __name__ == "__main__":
    main()
