# DigiEduHack (2025) - It worked yesterday
## 1. One-sentence description
A smart, all-in-one platform that uses AI to handle diverse data types—from processing and evaluation to storage and reporting.

## 2. Technology stack (languages, key libraries, AI models used)
* Docker
* Frontend: html, css, js
* Backend: FastAPI
* Websocket for persistent communication (Chatbot)
* Uppy and Tusd for file(s) upload
* AI models:
    * llama3.1:8b for data manipulation
    * embedded-ollama for chatbot
    * whisper for speech2text

## 3. Data Privacy Statement
* Where data is processed?
    * locally
* AI services used
    * models mentioned above
* Does data leave the EU?
    * no, everything is processed locally
* Monthly cost estimate:
    * **On-prem GPU amortized:**:
        * Electricity	€30–€40
        * Hardware amortization	€35–€40
        * Maintenance	€0–€20
    * Total monthly	€65–€100
    * All can be run on individual server (ofcourse we do not recommend that for data security and integrity)

## 4. Prerequisities
Docker Engine 24+ or Docker Desktop 4.27 <br>
[requirements.txt](/srcs/src/backend/requirements.txt) <br>
[uppy](https://uppy.io/docs/quick-start/) <br>
[tus.io](https://tus.github.io/tusd/getting-started/installation/) <br>
[whisper](https://github.com/openai/whisper) <br>
[metabase](https://www.metabase.com/), open source version under the GNU Affero General Public License (AGPL) <br>
[chromadb](https://www.trychroma.com/)

## 5. Setup instructions (copy-paste commands), 6. How to run locally
``` Docker
cd digiEduHack_hackathon/srcs/
docker compose up -d
```
Use the embedded Ollama container (default, more self-contained):
```
docker compose --profile embedded-ollama up -d
```
This launches the ollama service defined in docker-compose.yml so everything stays inside Docker.

Use an existing host Ollama (saves resources, skips the container):
```
OLLAMA_HOST=http://host.docker.internal:11434 docker compose up -d
```
Because the Ollama service sits behind the embedded-ollama profile, it will only start if you explicitly request that profile.
(On Linux we add host.docker.internal via extra_hosts, so this hostname resolves to your host automatically.)

Whichever option you choose, make sure the Ollama instance has both the chat model and the embedding model pulled. By default the code expects:
```
ollama pull llama3.1:8b        # chat model (OLLAMA_MODEL)
ollama pull embeddinggemma     # embedding model (OLLAMA_EMBED_MODEL)
```

### **1. ollama (local LLM server, optional profile)**

* Exposes port **11434** → override via `OLLAMA_PORT=<port>`.
* Stores downloaded models in the named docker volume `ollama_data`.
* Auto-pulls `llama3.1:8b` on startup via `chat/docker-entrypoint.sh`.

### **2. backend (FastAPI + SQLite)**

* Exposes REST API on **[http://localhost:8000](http://localhost:8000)**
* Uses SQLite database stored in `./data/app.db`
* Provides endpoints:

  * `POST/GET/PUT/DELETE /regions`
  * `POST/GET/PUT/DELETE /schools`
  * `POST/GET /files`

### Auto-reload during development

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

### File persistence

Everything you upload or store survives container restarts because all data lives on your host:

```
./data/
 ├── app.db            ← SQLite database (regions, schools, file metadata)
 └── uploads/          ← tusd-managed uploaded files
```

Delete this folder to wipe all app data.

---

### Environment variables

You can override defaults using `.env` or via inline `docker compose`:

| Variable               | Default                              | Used by                     |
| ---------------------- | ------------------------------------ | --------------------------- |
| `OLLAMA_HOST`          | `http://ollama:11434`                | backend, worker, embeddings |
| `OLLAMA_PORT`          | `11434`                              | ollama                      |
| `OLLAMA_MODEL`         | `llama3.1:8b`                        | backend / worker LLM calls  |
| `OLLAMA_EMBED_MODEL`   | `embeddinggemma`                     | embeddings in RAG           |
| `BACKEND_TEST_PROMPT`  | “Say hi from the backend container”  | backend demo script         |
| `DATABASE_URL`         | `sqlite:////data/app.db`             | backend                     |
| `TUSD_URL`             | `http://tusd:1080`                   | backend for linking uploads |

---

### Backend API Usage

List regions

```bash
curl http://localhost:8000/regions
```

Create a region

```bash
curl -X POST http://localhost:8000/regions \
     -H "Content-Type: application/json" \
     -d '{"name": "Hlavní město Praha"}'
```

Create a school in a region (FK)

```bash
curl -X POST http://localhost:8000/schools \
     -H "Content-Type: application/json" \
     -d '{"name": "Gymnazium Nad Alejí", "region_id": 1}'
```

---

### File Upload Flow (tusd → backend)

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

### Asking the LLM via Backend

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

### Direct Ollama API prompting

Generate

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:1.5b",
  "prompt": "Write a haiku about hackathons."
}'
```

Chat

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "deepseek-r1:1.5b",
  "messages": [
    {"role": "user", "content": "Explain REST APIs briefly."}
  ]
}'
```

---

Logs

```bash
docker compose logs -f         # all services
docker compose logs -f backend # backend only
docker compose logs -f ollama  # ollama only
docker compose logs -f tusd    # tusd only
```

---

Stop / clean up

```bash
docker compose stop        # graceful stop
docker compose down        # remove containers, keep volumes
docker compose down -v     # remove containers + ollama model volume
rm -rf ./data              # wipe DB + uploads
```

## 7. How to deploy to production
* Everything is running in Docker, so as far as you have running Docker, you should be fine.

## 8. Known limitations
* Hallucinations and factual inaccuracies – possible limitations linked to the smaller model size.
* Chatbot response time – may be slower because all processing runs on local hardware.
* Reporting features – still partially incomplete and require further refinement.
* Dependency on open source solutions could lead to lack of support/end of support.