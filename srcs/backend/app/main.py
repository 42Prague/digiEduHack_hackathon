from fastapi import FastAPI

from .db import init_db
from .routers import regions, schools, files

app = FastAPI(title="DigiEduHack Backend")

app.include_router(regions.router)
app.include_router(schools.router)
app.include_router(files.router)


@app.on_event("startup")
def on_startup():
    init_db()
