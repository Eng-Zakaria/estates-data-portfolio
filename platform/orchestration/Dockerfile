# P02 Airflow image: official 3.3.1 + estate ingest/dbt stack.
# Build: make airflow-build
FROM apache/airflow:3.3.1

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /tmp/requirements.txt
# --constraint keeps provider pins coherent with the base image.
RUN pip install --no-cache-dir --constraint \
    "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.1/constraints-3.12.txt" \
    -r /tmp/requirements.txt
