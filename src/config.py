
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username="weather_user",
    password=os.environ["POSTGRES_PASSWORD"],
    host=DATABASE_HOST,
    port=5432,
    database="weather_db",
)


def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
