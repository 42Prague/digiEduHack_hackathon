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

# Default model: llama3.1:8b
# Tmp for testing: deepseek-r1:1.5b

# if ! ollama list | grep -Fq 'deepseek-r1:1.5b'; then
#   echo "Downloading deepseek-r1:1.5b..."
#   ollama pull deepseek-r1:1.5b
# fi

# echo "deepseek-r1:1.5b ready. Serving requests."

if ! ollama list | grep -Fq 'llama3.1:8b'; then
  echo "Downloading llama3.1:8b..."
  ollama pull llama3.1:8b
fi

echo "llama3.1:8b ready. Serving requests."

wait "$SERVER_PID"
