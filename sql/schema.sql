
CREATE TABLE IF NOT EXISTS raw_weather (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name TEXT NOT NULL DEFAULT 'open-meteo',
    payload JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_weather (
    forecast_date DATE PRIMARY KEY,
    temp_max_c NUMERIC(5, 2),
    temp_min_c NUMERIC(5, 2),
    precipitation_mm NUMERIC(8, 2),
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_precipitation_nonnegative
        CHECK (
            precipitation_mm IS NULL
            OR precipitation_mm >= 0
        ),

    CONSTRAINT chk_temperature_range
        CHECK (
            temp_max_c IS NULL
            OR temp_min_c IS NULL
            OR temp_max_c >= temp_min_c
        )
);
