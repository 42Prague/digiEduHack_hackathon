
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import regions, schools, files, chat

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

@app.on_event("startup")
def on_startup():
    init_db()
