#!/bin/sh
set -eu

ollama serve &
SERVER_PID=$!

cleanup() {
  kill -TERM "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID"
}
trap cleanup INT TERM

until ollama list >/dev/null 2>&1; do
  sleep 1
done

if ! ollama list | grep -Fq 'llama3.1:8b'; then
  echo "Downloading llama3.1:8b..."
  ollama pull llama3.1:8b
fi

if ! ollama list | grep -Fq 'embeddinggemma'; then
  echo "Downloading embeddinggemma..."
  ollama pull embeddinggemma
fi

echo "llama3.1:8b and embeddinggemma ready. Serving requests."

wait "$SERVER_PID"
