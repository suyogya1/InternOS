import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import Base, engine
from . import models  # noqa: F401
from .routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="InternOS API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "./artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")

app.include_router(router)

@app.get("/")
def root():
    return {"ok": True, "name": "InternOS API", "artifacts": "/artifacts"}