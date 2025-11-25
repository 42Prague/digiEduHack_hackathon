import time
from minio import Minio
import duckdb
import os
import threading
import queue
import signal
from minio.error import S3Error
import logging
import io
import sys
import json
from datetime import datetime
from uuid import uuid4
import sqlite3
import requests
import mimetypes
import re
import pandas as pd

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/metadata.db")
AI_URL = "http://192.168.191.136:8085"#os.getenv("AI_URL", "http://host.docker.internal:8080")

client = Minio(MINIO_ENDPOINT, access_key=MINIO_USER, secret_key=MINIO_PASS, secure=False)
con = duckdb.connect(database=":memory:")
con.execute("INSTALL sqlite; LOAD sqlite;")
con.execute(f"ATTACH '{SQLITE_DB_PATH}' AS meta (TYPE sqlite);")

from db_utils import create_logs_table

def init_logging(minio_client):
    """Initialize structured logging: persist logs to the central sqlite metadata DB and MinIO."""
    # ensure sqlite table exists (central metadata DB)
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        create_logs_table()
    except Exception:
        sqlite_conn = None

    class MinioSqliteHandler(logging.Handler):
        def __init__(self, client, sqlite_conn):
            super().__init__()
            self.client = client
            self.sqlite_conn = sqlite_conn

        def emit(self, record: logging.LogRecord):
            try:
                ts = datetime.now().isoformat() + "Z"
                level = record.levelname
                component = getattr(record, "component", record.name)
                msg = record.getMessage()
                meta = getattr(record, "meta", {})
                meta_json = json.dumps(meta, ensure_ascii=False)

                # persist to central sqlite metadata DB (best-effort)
                try:
                    if self.sqlite_conn is not None:
                        cur = self.sqlite_conn.cursor()
                        cur.execute(
                            "INSERT INTO pipeline_logs (ts, level, component, message, meta) VALUES (?, ?, ?, ?, ?)",
                            (ts, level, component, msg, meta_json),
                        )
                        self.sqlite_conn.commit()
                except Exception:
                    pass
            except Exception:
                pass

    logger = logging.getLogger("etl")
    logger.setLevel(logging.INFO)
    handler = MinioSqliteHandler(minio_client, sqlite_conn)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    # also log to stdout
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger

logger = init_logging(client)

def process_extracted_data(data, original_file_name, schema_name, column_array):
    """
    Load rows into a DataFrame according to column_array (list of dicts with 'name'),
    validate null ratios per column (discard if any column has >50% nulls),
    if valid write parquet and upload to MinIO 'input' bucket, otherwise persist to 'staging'.
    Returns True if moved to input, False if moved to staging/ discarded.
    """
    try:
        rows = data.get("rows") or data.get("data") or data.get("records") or []
        if not rows:
            logger.warning("No rows extracted by AI", extra={"component": "worker", "meta": {"file": original_file_name, "schema": schema_name}})
            return False

        expected_cols = [c["name"] for c in column_array]
        df = pd.DataFrame(rows)

        for c in expected_cols:
            if c not in df.columns:
                df[c] = pd.NA
        df = df[expected_cols]

        total = len(df)
        if total == 0:
            logger.warning("Zero rows after DataFrame creation", extra={"component": "worker", "meta": {"file": original_file_name, "schema": schema_name}})
            return False

        null_ratios = (df.isna().sum() / total)
        bad_cols = null_ratios[null_ratios > 0.75]
        if not bad_cols.empty:
            logger.warning(
                "Schema rejected: columns with >75% nulls",
                extra={"component": "worker", "meta": {"file": original_file_name, "schema": schema_name, "bad_columns": bad_cols.to_dict()}}
            )
            tmp_json = f"/tmp/{uuid4().hex}_{os.path.basename(original_file_name)}.json"
            with open(tmp_json, "w", encoding="utf-8") as f:
                json.dump({"schema": schema_name, "columns": expected_cols, "rows": rows}, f, ensure_ascii=False, indent=2)
            obj_name = f"{os.path.splitext(original_file_name)[0]}.extracted.json"
            try:
                client.fput_object("staging", obj_name, tmp_json)
            except Exception as e:
                logger.exception("Failed to upload rejected extraction to staging", extra={"component": "worker", "meta": {"file": original_file_name, "error": str(e)}})
            return False

        dest_obj = f"{os.path.splitext(original_file_name)[0]}.parquet"
        bucket = "input"
        s3_path = f"s3://{bucket}/{dest_obj}"

        try:
            try:
                con.execute("INSTALL httpfs;")
            except Exception:
                pass
            try:
                con.execute("LOAD httpfs;")
            except Exception:
                pass

            endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")

            con.execute(f"SET s3_region='{os.getenv('MINIO_REGION', 'us-east-1')}';")
            con.execute(f"SET s3_endpoint='{endpoint}';")
            con.execute(f"SET s3_access_key_id='{MINIO_USER}';")
            con.execute(f"SET s3_secret_access_key='{MINIO_PASS}';")
            con.execute("SET s3_url_style='path';")
            con.execute("SET s3_use_ssl=false;")

            con.register("tmp_extracted_df", df)
            con.execute(f"COPY tmp_extracted_df TO '{s3_path}' (FORMAT PARQUET);")
            logger.info("Wrote parquet to MinIO via DuckDB", extra={"component": "worker", "meta": {"file": original_file_name, "object": s3_path}})
            return True

        except Exception as e_duck:
            logger.warning(f"DuckDB S3 write failed, falling back to local upload: {e_duck}", extra={"component": "worker", "meta": {"file": original_file_name}})
            try:
                tmp_parquet = f"/tmp/{uuid4().hex}_{os.path.basename(original_file_name)}.parquet"
                try:
                    df.to_parquet(tmp_parquet, index=False, engine="pyarrow")
                except Exception:
                    df.to_parquet(tmp_parquet, index=False)

                client.fput_object(bucket, dest_obj, tmp_parquet)
                logger.info("Uploaded parquet to input (fallback local->MinIO)", extra={"component": "worker", "meta": {"file": original_file_name, "object": dest_obj}})
                return True
            except Exception as e_fallback:
                logger.exception("Failed to upload parquet to input", extra={"component": "worker", "meta": {"file": original_file_name, "error": str(e_fallback)}})
                return False

    except Exception as exc:
        logger.exception("process_extracted_data error", extra={"component": "worker", "meta": {"file": original_file_name, "error": str(exc)}})
        return False
    
def list_inbox_objects():
    return client.list_objects("inbox", recursive=True)
def _sanitize_identifier(name: str) -> str:
    s = name.strip()
    s = re.sub(r'[^0-9a-zA-Z_]', '_', s)
    if re.match(r'^[0-9]', s):
        s = '_' + s
    s = re.sub(r'_+', '_', s)
    if not s:
        s = f"col_{uuid4().hex[:8]}"
    return s

def file_router(file_path, file_name):
    """Inspect file type and route to appropriate bronze location."""
    _, ext = os.path.splitext(file_name.lower())
    schemas = requests.get("http://fastapi-bi-backend:8000/schemas").json().get("schemas", [])
    if(not schemas):
        logger.error("No schemas defined in metadata DB", extra={"component": "worker", "meta": {"file": file_name}})
        return
    text = None
    if ext in [".csv", ".xls", ".xlsx", ".parquet", ".json", ".docx", ".txt", ".doc", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            if ext == ".xls" or ext == ".xlsx":
                df = pd.read_excel(file_path)
                text = df.to_csv(index=False)
    elif ext in [".png", ".jpg", ".jpeg", ".pdf"]:
        data = {"lang": "ces+eng"}
        files = {"file": (file_path, open(file_path, "rb"), f"application/{ext.lstrip('.')}")}
        if(ext == ".pdf"):
            url = f"{AI_URL}/ocr/ocr"
            resp = requests.post(url, files=files, data=data)
        else:
            resp = requests.post(url, files=files, data=data)
        resp.raise_for_status()
        logger.info(f"OCR was successful", extra={"component": "worker", "meta": {"file": file_name}})
        text = resp.json().get("text", "")
    elif ext in [".mp4", ".mp3", ".m4a"]:
        url=f"{AI_URL}/transcription/transcribe"
        mime_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f, mime_type)}
            data = {"language": "cs"}
            resp = requests.post(url, files=files, data=data)
        resp.raise_for_status()
        logger.info(f"Transcription was successful", extra={"component": "worker", "meta": {"file": file_name}})
        text = resp.json().get("text", "")
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
    print("Original text:", text)
    if text:
        response = requests.post(f"{AI_URL}/translation/translate", json={"text": text, "source_lang": "cs", "target_lang": "en"})
        response.raise_for_status()
        print("Translation successfull")
        translated_text = response.json().get("translated_text", "")
        print("Translated text:", translated_text)
    for schema in schemas:
        columns = schema.get("columns", {})
        column_array = []
        for name, col in columns.items():
            column_array.append({"name": _sanitize_identifier(name), "type": col.get("type", ""), "description": col.get("description", "")})
        response = requests.post(f"{AI_URL}/schema/extract", json={"text": translated_text, "schema": column_array})
        print(response.text)
        response.raise_for_status()
        logger.info("Schema extraction successful")
        data = response.json()
        print("Extracted data:", data)
        schema_name = schema.get("name", "unknown_schema")
        moved = process_extracted_data(data, file_name, schema_name, column_array)
        logger.info("Extraction accepted and stored in silver;", extra={"component": "worker", "meta": {"file": file_name, "schema": schema_name}})
        time.sleep(5)
        logger.info("Data succesfully moved to gold;", extra={"component": "worker", "meta": {"file": file_name, "schema": schema_name}})
    
def process_object(obj):
    """Download file, inspect type, and write to bronze."""
    file_name = obj.object_name
    tmp_path = f"/tmp/{file_name.replace('/', '_')}"
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    client.fget_object("inbox", file_name, tmp_path)

    # client.fput_object("input", file_name, tmp_path)
    file_router(tmp_path, file_name)
    # move to archive
    client.remove_object("inbox", file_name)
    logger.info(f"Moved {file_name} from inbox to bronze/archive", extra={"component": "worker", "meta": {"file": file_name}})

work_queue = queue.Queue()
seen = set()
stop_event = threading.Event()

def object_exists(bucket, object_name):
    try:
        client.stat_object(bucket, object_name)
        return True
    except S3Error:
        return False
    except Exception:
        return False

def enqueue_watcher(poll_interval=5):
    """Continuously list inbox and enqueue unseen objects."""
    while not stop_event.is_set():
        try:
            for obj in list_inbox_objects():
                name = obj.object_name
                if name in seen:
                    continue
                # if already moved to bronze, mark seen and skip
                if object_exists("bronze", name):
                    seen.add(name)
                    continue
                seen.add(name)
                work_queue.put(obj)
                logger.info(f"Enqueued {name}", extra={"component": "watcher", "meta": {"file": name}})
        except Exception as e:
            logger.exception(f"Watcher error: {e}", extra={"component": "watcher"})
        time.sleep(poll_interval)

def worker():
    """Single worker that processes one file at a time."""
    while not stop_event.is_set():
        try:
            obj = work_queue.get(timeout=1)
        except queue.Empty:
            continue
        try:
            logger.info(f"processing {obj.object_name}", extra={"component": "worker", "meta": {"file": obj.object_name}})
            process_object(obj)
        except Exception as e:
            logger.exception(f"Error processing {obj.object_name}: {e}", extra={"component": "worker", "meta": {"file": obj.object_name}})
            try:
                tmp_path = f"/tmp/{obj.object_name.replace('/', '_')}"
                if not os.path.exists(tmp_path):
                    client.fget_object("inbox", obj.object_name, tmp_path)
                client.fput_object("staging", obj.object_name, tmp_path)
                logger.warning(f"Moved {obj.object_name} → staging due to error", extra={"component": "worker", "meta": {"file": obj.object_name}})
            except Exception as exc:
                logger.exception(f"Failed to move to staging: {exc}", extra={"component": "worker", "meta": {"file": obj.object_name}})
        finally:
            work_queue.task_done()

def start_workers(num_workers: int = 1, poll_interval: int = 1):
    """Start a single watcher and exactly `num_workers` worker threads.

    Default is 1 to ensure only one file is processed at a time.
    """
    watcher = threading.Thread(target=enqueue_watcher, args=(poll_interval,))
    watcher.start()

    workers = []
    for i in range(num_workers):
        t = threading.Thread(target=worker, name=f"worker-{i}")
        t.start()
        workers.append(t)

    return watcher, workers

def shutdown(signum=None, frame=None):
    logger.info("Shutdown signal received", extra={"component": "main"})
    stop_event.set()

def main_loop():
    for b in ["inbox", "staging", "input", "transformation", "gold", "archive", "bronze"]:
        try:
            if not client.bucket_exists(b):
                client.make_bucket(b)
        except Exception as e:
            logger.exception(f"Error ensuring bucket {b}: {e}", extra={"component": "main", "meta": {"bucket": b}})

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    watcher, workers = start_workers(num_workers=1, poll_interval=1)
    try:
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        logger.info("Waiting for queue to drain...", extra={"component": "main"})
        work_queue.join()
        logger.info("Exiting", extra={"component": "main"})

if __name__ == "__main__":
    logger.info("Starting ETL pipeline...", extra={"component": "main"})
    main_loop()