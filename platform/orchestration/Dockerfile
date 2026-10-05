# P02 Airflow image: official 3.3.1 + estate ingest/dbt stack.
# Build: make airflow-build
FROM apache/airflow:3.3.1

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /tmp/requirements.txt
# NOTE: constraints files are only for the apache-airflow install step itself
# (see the constraints header). Our layer installs without constraints but pins
# apache-airflow==3.3.1 in requirements to prevent accidental up/downgrade.
RUN pip install --no-cache-dir -r /tmp/requirements.txt
