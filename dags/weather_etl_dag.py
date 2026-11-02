
import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/weather-data-pipeline"

default_args = {
    "retries": 2,
    "retry_delay": pendulum.duration(minutes=5),
    "execution_timeout": pendulum.duration(minutes=10),
}

with DAG(
    dag_id="weather_etl_pipeline",
    description="Extract, transform, and load weather data",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["data-engineering", "etl", "weather"],
) as dag:

    extract = BashOperator(
        task_id="extract_weather",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.ingest"
        ),
        do_xcom_push=True,
    )

    transform = BashOperator(
        task_id="transform_weather",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.transform "
            "'{{ ti.xcom_pull(task_ids=\"extract_weather\") }}'"
        ),
        do_xcom_push=True,
    )

    load = BashOperator(
        task_id="load_weather",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m src.load "
            "'{{ ti.xcom_pull(task_ids=\"extract_weather\") }}' "
            "'{{ ti.xcom_pull(task_ids=\"transform_weather\") }}'"
        ),
    )

    extract >> transform >> load
