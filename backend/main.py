from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from database.models import init_db
from routers import documents, scans, humanize
from services.plagiarism_engine import PlagiarismEngine
from services.humanizer import HumanizerService


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.plagiarism_engine = PlagiarismEngine()
    app.state.humanizer_service = HumanizerService()
    yield


app = FastAPI(
    title="Plagiarism Checker & Humanizer",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(humanize.router, prefix="/api/humanize", tags=["humanize"])


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check():
    return {"status": "ok"}
