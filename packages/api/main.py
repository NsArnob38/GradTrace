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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://grad-trace.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Custom 422 Logging & Sanitization
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log 422 errors and SANITIZE them into a string to prevent frontend crashes."""
    errors = exc.errors()
    # Flatten the errors into a single readable string
    # e.g., "body.program: field required, body.concentration: invalid string"
    error_msgs = []
    for error in errors:
        loc = ".".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "Unknown error")
        error_msgs.append(f"{loc}: {msg}")
    
    flattened_error = ", ".join(error_msgs)
    
    print(f"DEBUG: 422 Validation Error at {request.url}")
    print(f"Entity body: {exc.body}")
    print(f"Flattened Errors: {flattened_error}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": flattened_error, "body": str(exc.body)},
    )

# CORS
# ... (rest of the file as before)

# Routes

# Routes
app.include_router(auth.router)
app.include_router(transcripts.router)
app.include_router(rubric.router)    # Important: Must come BEFORE audit.router so literal paths like /audit/level1 are caught before /audit/{id}
app.include_router(audit.router)
app.include_router(admin_auth.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gradetrace-api"}
