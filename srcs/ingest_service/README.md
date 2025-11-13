# Ingestion Service

FastAPI-based backend that ingests three kinds of artifacts coming from workshops:

- **Audio recordings** - stores raw files, runs local Whisper transcription via `faster-whisper`, and saves transcripts into `audio_recording`.
- **Survey exports** - accepts CSV/XLSX/JSON dumps (Google Forms, Typeform, etc.), normalizes teacher metadata, and writes rows into `survey_response`.
- **Raw documents** - buckets everything else (PDF, text, random tables) into `raw_document` together with any extracted text/table content.

## Database schema

| Table | Purpose | Key fields |
| --- | --- | --- |
| `teacher` | Canonical teacher records. | `id`, `full_name`, `normalized_name`, `email` |
| `audio_recording` | Uploaded audio files + Whisper transcript. | `id (UUID)`, `teacher_id`, `workshop_id`, `audio_path`, `transcript_text`, `duration_sec` |
| `survey_response` | Normalized survey rows. | `id`, `teacher_id`, `workshop_id`, `submitted_at`, `raw_data`, `normalized_data` |
| `raw_document` | Generic file bucket. | `id (UUID)`, `doc_type`, `teacher_id`, `workshop_id`, `file_path`, `text_content`, `table_data` |

`DATABASE_URL` (e.g. `postgresql+psycopg2://user:pass@host:5432/db`) must be defined before starting the app.

## API

- `GET /health` - returns `{"status": "ok"}` once the service and DB connection are alive.
- `POST /audio/upload` - multipart upload of an audio file (`file` field) plus optional `teacher_id`/`workshop_id`. Stores the file, runs Whisper transcription, and returns an `AudioResult`.
- `POST /survey/ingest` - multipart upload of a survey export (`file` field) with optional `workshop_id`. Parses via pandas, resolves teachers, inserts rows, and reports `SurveyIngestResult`.
- `POST /raw/ingest` - multipart upload of any file (`file` field) plus optional `doc_type`, `teacher_id`, `workshop_id`. Saves into `raw_document` with extracted text/table data when possible, returning `RawIngestResult`.

All endpoints return structured `ApiError` objects when something cannot be processed.

## Local development

```bash
cd ingest_service
python -m venv .venv
. .venv/Scripts/activate  # Windows
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/ingest
uvicorn main:app --reload
```

Visit `http://localhost:8000/health` to confirm deployment.

## Docker

```bash
cd ingest_service
docker build -t ingestion-service .
docker run -e DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db -p 8000:8000 ingestion-service
```

Mount a volume to `/app/data` if you want to persist uploaded files outside the container.

## Architecture overview

- **FastAPI** drives HTTP routing and dependency injection.
- **SQLAlchemy** (ORM) manages PostgreSQL access; `Base.metadata.create_all()` bootstraps the schema for hackathon speed.
- **faster-whisper** runs local speech-to-text with configurable model/device via environment variables.
- **pandas** powers tabular ingestion for both surveys and arbitrary spreadsheets.
- Files are stored under `ingest_service/data` (overridable via `INGEST_DATA_DIR`) so the service can keep raw assets alongside structured DB records.
