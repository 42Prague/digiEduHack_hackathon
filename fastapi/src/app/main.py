from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from minio import Minio
from minio.error import S3Error
import os
from datetime import datetime, timedelta
import io
from typing import Optional, Dict
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from uuid import uuid4
import json

from src.app.db_utils import get_user, verify_password, insert_schema_metadata, add_column_to_schema, get_logs
class SchemaRegistration(BaseModel):
    schema_name: str
    columns: Dict[str, Dict[str, str]]
    overwrite: Optional[bool] = False
    description: Optional[str] = ""

app = FastAPI(title="Data Lake Ingestion API")

# Get MinIO endpoint from environment, supporting both MINIO_ENDPOINT and MINIO_URL
MINIO_ENDPOINT_RAW = os.getenv("MINIO_ENDPOINT") or os.getenv("MINIO_URL", "minio:9000")
# Minio client expects just host:port, no protocol or path
# Strip http:// or https:// prefix if present
MINIO_ENDPOINT = MINIO_ENDPOINT_RAW.replace("http://", "").replace("https://", "")
# Strip any path components (everything after /)
if "/" in MINIO_ENDPOINT:
    MINIO_ENDPOINT = MINIO_ENDPOINT.split("/")[0]
MINIO_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_USER,
    secret_key=MINIO_PASS,
    secure=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(files: list[UploadFile] = File(...)):
    """Upload multiple files to MinIO inbox."""
    results = []
    for file in files:
        try:
            content = await file.read()
            file_name = f"{datetime.now().isoformat()}_{uuid4().hex}_{file.filename}"
            stream = io.BytesIO(content)
            minio_client.put_object(
                bucket_name="inbox",
                object_name=file_name,
                data=stream,
                length=len(content),
                content_type=file.content_type,
            )
            await file.close()
            results.append({"file_name": file_name, "status": "ok"})
        except S3Error as e:
            results.append({"file_name": getattr(file, "filename", None), "status": "error", "detail": f"MinIO error: {e}"})
        except Exception as e:
            results.append({"file_name": getattr(file, "filename", None), "status": "error", "detail": str(e)})
    return {"results": results}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Admin login route returning JWT token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/schemas/register")
async def register_schema(payload: SchemaRegistration):
    """
    Generic endpoint to register a schema. Payload example:
    {
      "schema_name": "my_schema_v1",
      "columns": {"col1": {"type": "string", "description": "smt"}, "col2": {"type": "date", "description": "date column"}},
      "description": "description"
    }
    Stores columns in the new format with type and description.
    """
    # Pass columns directly - they're already in the correct format
    # Format: {"col1": {"type": "string", "description": "..."}}
    ok = insert_schema_metadata(payload.schema_name, payload.columns, payload.description or "")
    if ok:
        return {"status": "ok", "schema": payload.schema_name}
    raise HTTPException(status_code=500, detail="Failed to register schema")

@app.put("/schemas/update")
async def update_schema(payload: SchemaRegistration):
    """
    Update an existing schema. Same payload as /schemas/register.
    Passes the full column structure (with type and description) to add_column_to_schema.
    """
    # Pass the columns directly - add_column_to_schema now supports the nested format
    # Format: {"col1": {"type": "string", "description": "..."}}
    ok = add_column_to_schema(payload.schema_name, payload.columns, payload.overwrite)
    if ok:
        return {"status": "ok", "schema": payload.schema_name}
    raise HTTPException(status_code=500, detail="Failed to update schema")

@app.get("/schemas")
async def list_schemas():
    """List all registered schemas."""
    try:
        from src.app.db_utils import get_conn
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT schema_name, columns, description FROM schema_metadata")
            rows = cur.fetchall()
            schemas = []
            for row in rows:
                raw_cols = row[1]
                if raw_cols is None or raw_cols == "":
                    columns = {}
                elif isinstance(raw_cols, (dict, list)):
                    columns = raw_cols
                else:
                    try:
                        columns = json.loads(raw_cols)
                    except (json.JSONDecodeError, TypeError):
                        columns = {}
                schemas.append({
                    "schema_name": row[0],
                    "columns": columns,
                    "description": row[2]
                })
        return {"schemas": schemas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schemas: {e}")

@app.get("/logs")
async def fetch_logs(from_date: str):
    """Fetch structured logs from the metadata database."""
    try:
        logs = get_logs(from_date)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {e}")