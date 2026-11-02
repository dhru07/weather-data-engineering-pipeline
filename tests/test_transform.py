
import pytest

from src.transform import transform_weather_data


@pytest.fixture
def sample_weather_data():
    """Provide predictable sample data for testing."""
    return {
        "daily": {
            "time": ["2026-10-29", "2026-10-30"],
            "temperature_2m_max": [31.2, 30.8],
            "temperature_2m_min": [20.1, 19.8],
            "precipitation_sum": [0.0, 1.2],
        }
    }


def test_transform_returns_expected_records(sample_weather_data):
    df = transform_weather_data(sample_weather_data)

    assert len(df) == 2
    assert list(df["forecast_date"].astype(str)) == [
        "2026-10-29",
        "2026-10-30",
    ]
    assert df.loc[0, "temp_max_c"] == 31.2
    assert df.loc[0, "temp_min_c"] == 20.1
    assert df.loc[1, "precipitation_mm"] == 1.2


def test_ingestion_timestamp_is_present(sample_weather_data):
    df = transform_weather_data(sample_weather_data)

    assert "ingested_at_utc" in df.columns
    assert df["ingested_at_utc"].notna().all()


def test_missing_daily_section_is_rejected():
    with pytest.raises(ValueError, match="daily"):
        transform_weather_data({})


def test_missing_required_field_is_rejected():
    data = {
        "daily": {
            "time": ["2026-10-29"],
        }
    }

    with pytest.raises(ValueError, match="Missing fields"):
        transform_weather_data(data)


def test_mismatched_array_lengths_are_rejected():
    data = {
        "daily": {
            "time": ["2026-10-29", "2026-10-30"],
            "temperature_2m_max": [31.2],
            "temperature_2m_min": [20.1, 19.8],
            "precipitation_sum": [0.0, 1.2],
        }
    }

    with pytest.raises(ValueError, match="length"):
        transform_weather_data(data)


def test_duplicate_dates_are_rejected():
    data = {
        "daily": {
            "time": ["2026-10-29", "2026-10-29"],
            "temperature_2m_max": [31.2, 30.8],
            "temperature_2m_min": [20.1, 19.8],
            "precipitation_sum": [0.0, 1.2],
        }
    }

    with pytest.raises(ValueError, match="Duplicate"):
        transform_weather_data(data)


def test_negative_precipitation_is_rejected():
    data = {
        "daily": {
            "time": ["2026-10-29"],
            "temperature_2m_max": [31.2],
            "temperature_2m_min": [20.1],
            "precipitation_sum": [-1.0],
        }
    }

    with pytest.raises(ValueError, match="Negative precipitation"):
        transform_weather_data(data)


def test_maximum_temperature_below_minimum_is_rejected():
    data = {
        "daily": {
            "time": ["2026-10-29"],
            "temperature_2m_max": [18.0],
            "temperature_2m_min": [20.0],
            "precipitation_sum": [0.0],
        }
    }

    with pytest.raises(ValueError, match="Maximum temperature"):
        transform_weather_data(data)


def test_non_numeric_temperature_is_rejected():
    data = {
        "daily": {
            "time": ["2026-10-29"],
            "temperature_2m_max": ["not-a-number"],
            "temperature_2m_min": [20.1],
            "precipitation_sum": [0.0],
        }
    }

    with pytest.raises((ValueError, TypeError)):
        transform_weather_data(data)
