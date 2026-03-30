"""
GradeTrace API — FastAPI Application

Main entry point for the backend API server.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from packages.api.config import get_settings
from packages.api.routes import auth, transcripts, audit, admin_auth, rubric

import os
settings = get_settings()

app = FastAPI(
    title="GradeTrace API",
    description="Academic transcript auditing platform for NSU",
    version="0.1.0",
)

# Startup Checks
@app.on_event("startup")
async def startup_event():
    print("\n--- API STARTUP CHECKS ---")
    if not settings.google_credentials_json:
        print("⚠️  WARNING: GOOGLE_CREDENTIALS_JSON is NOT set. OCR for scanned PDFs will be disabled.")
    else:
        try:
            import json
            json.loads(settings.google_credentials_json)
            print("✅ GOOGLE_CREDENTIALS_JSON detected and appears to be valid JSON.")
        except Exception as e:
            print(f"❌ ERROR: GOOGLE_CREDENTIALS_JSON is set but is NOT valid JSON: {str(e)}")
    print("--- END STARTUP CHECKS ---\n")

# Custom 422 Logging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log 422 errors to the console so the developer can see exactly what field failed."""
    print(f"DEBUG: 422 Validation Error at {request.url}")
    print(f"Entity body: {exc.body}")
    print(f"Errors: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

# CORS
# ... (rest of the file as before)

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
