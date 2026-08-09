import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.interview import router as interview_router

load_dotenv()

app = FastAPI(title="AI Interview Agent API")

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
allowed_origins = [
    origin.strip()
    for origin in allowed_origins_raw.split(",")
    if origin.strip()
]
if not allowed_origins:
    allowed_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "AI Interview Agent API is running",
        "health": "/health",
        "docs": "/docs",
        "frontend": "http://localhost:3000/"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
