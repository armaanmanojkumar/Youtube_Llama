import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from .routes import ingest, query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("rag").info("YouTube LLaMA backend started")
    yield
    logging.getLogger("rag").info("YouTube LLaMA backend shutting down")


app = FastAPI(title="YouTube LLaMA Studio", lifespan=lifespan)

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(query.router)


@app.get("/")
def root():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "YouTube LLaMA Studio backend is running."}
