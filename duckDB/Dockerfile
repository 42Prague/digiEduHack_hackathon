# Use official Python runtime as base image
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && rm -rf /var/lib/apt/lists/*

RUN pip install duckdb watchfiles pandas minio boto3 python-jose bcrypt requests openpyxl

ENTRYPOINT ["sh", "-c", "watchfiles 'python -u /app/scripts/run_pipeline.py' /app/scripts/"]

# "watchfiles" python /app/scripts/run_pipeline.py "/app/scripts/"

