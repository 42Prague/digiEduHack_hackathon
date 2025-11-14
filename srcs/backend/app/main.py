from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api import chat
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import regions, schools, files

app = FastAPI(title="DigiEduHack Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(regions.router)
app.include_router(schools.router)
app.include_router(files.router)

static_path = Path(__file__).parent / "static"
print(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.on_event("startup")
def on_startup():
    init_db()
