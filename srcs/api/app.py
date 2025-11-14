import asyncio
import json
import os
import random
import shutil
import time
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from datetime import datetime

from srcs.dq.data_quality import DataQualityProcessor

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# In-memory user store
# ---------------------------------------------------------------------

USER_STORE = {}  # { username: { "password": str, "role": "uploader"|"analyst" } }


# ---------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------
@app.post("/register")
def register(username: str, password: str, role: str):
    if username in USER_STORE:
        raise HTTPException(status_code=400, detail="user exists")
    if role not in ("uploader", "analyst"):
        raise HTTPException(status_code=400, detail="invalid role")
    USER_STORE[username] = {"password": password, "role": role}
    return {"ok": True}


# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------
@app.post("/login")
def login(username: str, password: str):
    u = USER_STORE.get(username)
    if not u or u["password"] != password:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"ok": True, "role": u["role"]}


# ---------------------------------------------------------------------
# Chat for analyst
# ---------------------------------------------------------------------
class AnalystChatRequest(BaseModel):
    message: str


CHART_DIR = Path("srcs/api/chart_samples")
CHART_PATHS = sorted(CHART_DIR.glob("debug_chart*.json"))

print(CHART_PATHS)

CHART_VARIANTS = []
for path in CHART_PATHS:
    with open(path, "r", encoding="utf-8") as f:
        CHART_VARIANTS.append(json.load(f))

# ---------------------------------------------------------
# Text variants
# ---------------------------------------------------------

TEXT_VARIANTS = [
    "Generated long text variant A. " * 60,
    "Generated long text variant B. " * 60,
    "Generated long text variant C. " * 60,
]

# ---------------------------------------------------------
# Endpoint
# ---------------------------------------------------------


@app.post("/analyst_chat")
async def analyst_chat(payload: AnalystChatRequest):
    await asyncio.sleep(1.0)

    answer = f"dummy response to: {payload.message}"

    choice = random.randint(1, 3)

    # here call agent(payload.message)
    # and agent returns basic answer (required), text_summary (opt.), chart_details (opt.)

    if choice == 1:
        return {
            "answer": answer,
            "generated_text": random.choice(TEXT_VARIANTS),
            "chart_details": None,
        }

    if choice == 2:
        return {
            "answer": answer,
            "generated_text": None,
            "chart_details": random.choice(CHART_VARIANTS),
        }

    return {
        "answer": answer,
        "generated_text": random.choice(TEXT_VARIANTS),
        "chart_details": random.choice(CHART_VARIANTS),
    }


# ---------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------
@app.post("/upload_document_files")
async def upload_files(
    files: List[UploadFile] = File(...),
    region: str = Form(...),
    school: str = Form(...),
    activity: str = Form(...),
):
    """
    This endpoint accepts multiple file uploads along with text form data
    for region, school, and activity.

    It saves each file with a unique timestamped name and returns a
    single status message upon successful completion.
    """

    # You can now use the string parameters, for example, to log them
    # or decide on a storage path.
    print(f"Received data for:")
    print(f"  Region: {region}")
    print(f"  School: {school}")
    print(f"  Activity: {activity}")
    print(f"  Files: {[file.filename for file in files]}")

    metadata = {
        "Region": region,
        "School": school,
        "Activity": activity,
        "Ingestion_time": datetime.now().isoformat(),
    }

    print(metadata)

    dq = DataQualityProcessor()
    unique_filenames = []

    for file in files:
        try:
            # Generate a unique filename
            file_extension = os.path.splitext(file.filename)[1]
            epoch_timestamp = int(time.time())
            base_filename = os.path.basename(file.filename).split(".")[0]

            # Note: You could also incorporate region/school/activity into the filename
            # or a directory structure if needed.
            unique_filename = f"{base_filename}_{epoch_timestamp}{file_extension}"
            unique_filenames.append(unique_filename)

            # Save the file
            with open(unique_filename, "wb") as f:
                # Use await for async file operations
                await file.seek(0)
                shutil.copyfileobj(file.file, f)

            dq.process(unique_filename, metadata)

        except Exception as e:
            print(e)
            # If any file fails, raise an exception
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file {file.filename}: {str(e)}",
            )

        finally:
            # Always close the file handle
            await file.close()

    for file in unique_filenames:
        Path(file).unlink()

    # If all files are processed without error, return a success status
    return JSONResponse(
        content={
            "status": "success",
            "message": f"Successfully uploaded {len(files)} files and saved data.",
        }
    )
