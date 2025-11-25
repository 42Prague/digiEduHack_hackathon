#!/bin/bash
set -e

echo "Starting FastAPI backend initialization..."


# Then start FastAPI
echo "Starting FastAPI server..."
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

