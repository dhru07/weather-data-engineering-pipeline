
FROM apache/airflow:3.3.2

USER root

COPY airflow-requirements.txt /requirements.txt

USER airflow

RUN pip install --no-cache-dir \
    -r /requirements.txt
