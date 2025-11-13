# Ollama + Backend Stack (`digiEduHack_hackathon/srcs`)

This directory is the control center for the local LLM playground:
- `chat/` holds the Ollama container entrypoint script.
- `backend/` contains a tiny Python client that calls the Ollama HTTP API and prints the reply.
- `docker-compose.yml` wires both pieces together so you can spin up everything with a single command.

## Prerequisites
- Docker Engine 24+ or Docker Desktop 4.27+ with Compose v2.
- (Optional) NVIDIA GPU + NVIDIA Container Toolkit if you need GPU acceleration on Linux.

## Start the stack
```bash
cd digiEduHack_hackathon/srcs
docker compose up -d
```
- Port `11434` from the `ollama` container is exposed by default; override it via `OLLAMA_PORT=<hostPort>` if needed.
- Downloaded models/configs live in the named volume `ollama_data`. Remove it with `docker compose down -v` to reclaim space.
- Both services start, but the Python backend simply idles (it runs `sleep infinity`) until you exec into it to send a request.
- Export env vars before running (or pass them inline) to tweak behavior:
  - `OLLAMA_MODEL` (default `deepseek-r1:1.5b`)
  - `BACKEND_TEST_PROMPT` (default “Say hi from the backend container”)
- Tail container output when debugging:
  ```bash
  docker compose logs -f
  docker compose logs -f backend   # backend only
  docker compose logs -f ollama    # ollama only
  ```

## Trigger backend prompts on demand
With both containers running you can exec into the backend whenever you want to send a request.
1. **Run with the default prompt**
   ```bash
   docker compose exec backend python app.py
   ```

2. **Inline custom prompt**
   ```bash
   docker compose exec \
     -e BACKEND_TEST_PROMPT="List three study tips" \
     backend python app.py
   ```

3. **Switch models for a single run**
   ```bash
   docker compose exec \
     -e OLLAMA_MODEL="llama3.1:8b" \
     backend python app.py
   ```

4. **Combine multiple overrides**
   ```bash
   docker compose exec \
     -e BACKEND_TEST_PROMPT="Summarize the benefits of pair programming" \
     -e OLLAMA_MODEL="deepseek-r1:1.5b" \
     backend python app.py
   ```

## Direct API prompting (no backend helper)
1. **`generate` endpoint**
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "deepseek-r1:1.5b",
     "prompt": "Write a haiku about hackathons."
   }'
   ```

2. **`chat` endpoint with multi-turn messages**
   ```bash
   curl http://localhost:11434/api/chat -d '{
     "model": "deepseek-r1:1.5b",
     "messages": [
       {"role": "user", "content": "You are a mentor. Help me debug a Python bug."},
       {"role": "user", "content": "Why is my list comprehension slower than a loop?"}
     ]
   }'
   ```

## Auto-installed model
The entrypoint (`chat/docker-entrypoint.sh`) ensures `deepseek-r1:1.5b` is available before the server starts. Update the script or run `docker compose exec ollama ollama pull <model>` if you want something else cached up front.

## GPU usage
Uncomment the `deploy.resources` block in `docker-compose.yml` to reserve all available NVIDIA GPUs on Linux (requires the NVIDIA Container Toolkit). On Docker Desktop for macOS/Windows, enable GPU access through the UI if your hardware supports it—no compose change needed.

## Stop / clean up
```bash
docker compose stop        # Graceful stop
docker compose down        # Stop and keep the volume
docker compose down -v     # Stop and delete downloaded models/configs
```
