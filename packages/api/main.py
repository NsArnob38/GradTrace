"""
GradeTrace API — FastAPI Application

Main entry point for the backend API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.api.config import get_settings
from packages.api.routes import auth, transcripts, audit, admin

import os
settings = get_settings()
print("DEBUG CORS_ORIGINS env:", os.environ.get("CORS_ORIGINS"))
print("DEBUG settings.cors_origins:", settings.cors_origins)

app = FastAPI(
    title="GradeTrace API",
    description="Academic transcript auditing platform for NSU",
    version="0.1.0",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(transcripts.router)
app.include_router(audit.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gradetrace-api"}


@app.get("/debug-cors")
async def debug_cors():
    return {
        "cors_origins_env": os.environ.get("CORS_ORIGINS"),
        "cors_origins_settings": settings.cors_origins,
    }
