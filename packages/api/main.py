"""
GradeTrace API — FastAPI Application

Main entry point for the backend API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.api.config import get_settings
from packages.api.routes import auth, transcripts, audit, admin_auth, rubric

import os
settings = get_settings()

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
app.include_router(rubric.router)    # Important: Must come BEFORE audit.router so literal paths like /audit/level1 are caught before /audit/{id}
app.include_router(audit.router)
app.include_router(admin_auth.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gradetrace-api"}
