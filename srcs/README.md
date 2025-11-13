# This directory contains the full local stack used for:

* Running a **local LLM** (via Ollama)
* Serving a **Python FastAPI backend** with CRUD endpoints for:

  * `regions`
  * `schools` (FK → region)
  * `files` (tus upload metadata)
* Handling **file uploads** using a separate `tusd` container
* Persisting **all data** (SQLite DB + uploaded files) in a shared `./data` folder on your host

Everything runs through **Docker Compose**, so you can start/stop the whole environment with a single command.

---

# Prerequisites

* Docker Engine 24+ or Docker Desktop 4.27+
* (Optional) NVIDIA GPU + NVIDIA Container Toolkit if you want GPU-accelerated LLM inference on Linux

---

# 🏁 Start the full stack

```bash
cd digiEduHack_hackathon/srcs
docker compose up -d
```

This boots three services:

### **1. ollama (local LLM server)**

* Exposes port **11434** → override via `OLLAMA_PORT=<port>`.
* Stores downloaded models in the named docker volume `ollama_data`.
* Auto-pulls `deepseek-r1:1.5b` on startup via `chat/docker-entrypoint.sh`.

### **2. backend (FastAPI + SQLite)**

* Exposes REST API on **[http://localhost:8000](http://localhost:8000)**
* Uses SQLite database stored in `./data/app.db`
* Provides endpoints:

  * `POST/GET/PUT/DELETE /regions`
  * `POST/GET/PUT/DELETE /schools`
  * `POST/GET /files`

### 🔄 Auto-reload during development

The Docker image now launches Uvicorn with `--reload`, so `docker compose up backend` will automatically restart the API when files under `app/` change. If you ever need a production-like run, override the command (e.g., `docker compose run backend uvicorn app.main:app --host 0.0.0.0 --port 8000`) to drop the reload flag.

### **3. tusd (file upload server)**

* Exposes port **1080**
* Stores uploaded file chunks & metadata in `./data/uploads/`

### **4. frontend (EduZmena file upload UI)**

* Builds from `./eduzmena-frontend/file-upload`
* Runs [`live-server`](https://www.npmjs.com/package/live-server) inside the container
* Serves the static upload UI on **[http://localhost:4173](http://localhost:4173)**
* Talks to the backend (`http://localhost:8000`) and tusd (`http://localhost:1080`) by default

Both `backend` and `tusd` access `/data` through a **shared bind mount**.

---

# 🌍 File persistence

Everything you upload or store survives container restarts because all data lives on your host:

```
./data/
 ├── app.db            ← SQLite database (regions, schools, file metadata)
 └── uploads/          ← tusd-managed uploaded files
```

Delete this folder to wipe all app data.

---

# ⚙️ Environment variables

You can override defaults using `.env` or via inline `docker compose`:

| Variable              | Default                             | Used by                     |
| --------------------- | ----------------------------------- | --------------------------- |
| `OLLAMA_PORT`         | `11434`                             | ollama                      |
| `OLLAMA_MODEL`        | `deepseek-r1:1.5b`                  | backend                     |
| `BACKEND_TEST_PROMPT` | “Say hi from the backend container” | backend demo script         |
| `DATABASE_URL`        | `sqlite:////data/app.db`            | backend                     |
| `TUSD_URL`            | `http://tusd:1080`                  | backend for linking uploads |

---

# 🧪 Backend API Usage

### List regions

```bash
curl http://localhost:8000/regions
```

### Create a region

```bash
curl -X POST http://localhost:8000/regions \
     -H "Content-Type: application/json" \
     -d '{"name": "Hlavní město Praha"}'
```

### Create a school in a region (FK)

```bash
curl -X POST http://localhost:8000/schools \
     -H "Content-Type: application/json" \
     -d '{"name": "Gymnazium Nad Alejí", "region_id": 1}'
```

---

# 📤 File Upload Flow (tusd → backend)

1. **Upload file to tusd**

   ```bash
   curl -X POST http://localhost:1080/files
   ```

   (returns a `tus_id`)

2. **Save metadata in backend**

   ```bash
   curl -X POST \
     "http://localhost:8000/files?tus_id=<id>&filename=doc.pdf&school_id=1"
   ```

The backend stores `tus_id`, `filename`, and school association.

---

# 🤖 Asking the LLM via Backend

Exec into backend and run its test script:

```bash
docker compose exec backend python app.py
```

Override prompt or model:

```bash
docker compose exec \
  -e BACKEND_TEST_PROMPT="List three study tips" \
  backend python app.py
```

---

# 📡 Direct Ollama API prompting

### Generate

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:1.5b",
  "prompt": "Write a haiku about hackathons."
}'
```

### Chat

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "deepseek-r1:1.5b",
  "messages": [
    {"role": "user", "content": "Explain REST APIs briefly."}
  ]
}'
```

---

# 🖥 Logs

```bash
docker compose logs -f         # all services
docker compose logs -f backend # backend only
docker compose logs -f ollama  # ollama only
docker compose logs -f tusd    # tusd only
```

---

# 🛑 Stop / clean up

```bash
docker compose stop        # graceful stop
docker compose down        # remove containers, keep volumes
docker compose down -v     # remove containers + ollama model volume
rm -rf ./data              # wipe DB + uploads
```
