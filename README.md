# GradeTrace — Academic Audit System
*(CSE226 Project Submission)*

A powerful, modular platform designed to audit academic transcripts for North South University (NSU) students, specifically tailored for CSE and BBA programs. The system features a unified Python audit engine, a FastAPI backend, and a modern Next.js React frontend.

## 🏗️ Architecture Diagram

```text
+---------------------+         +----------------------+         +---------------------+
|                     |         |                      |         |                     |
|  Next.js Frontend   |         |    FastAPI Server    |         |  Supabase Database  |
|  (packages/web/)    | <=====> |   (packages/api/)    | <=====> |  (PostgreSQL Auth)  |
|                     |  REST   |                      |  ORM    |                     |
+---------------------+         +----------------------+         +---------------------+
                                          |
                                          v
                                +----------------------+
                                |                      |
                                | Python Audit Engine  |
                                |  (packages/core/)    |
                                |                      |
                                +----------------------+
```

---

## 🚀 How to Run Locally

### 1. Run the FastAPI Backend (API)
The backend engine handles all transcript parsing, CGPA calculation, and graduation logic.

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start the API server
python -m uvicorn packages.api.main:app --port 8000 --reload
```
*The API will be available at `http://localhost:8000`*
*Interactive Docs (Swagger UI) available at `http://localhost:8000/docs`*

### 2. Run the Next.js Web Frontend
The frontend dashboard visualizes the API data without performing client-side logic.

```bash
# 1. Navigate to the web package
cd packages/web

# 2. Install Node dependencies
npm install

# 3. Start the dev server
npm run dev
```
*The web dashboard will be available at `http://localhost:3000`*

### 3. Local MCP Server

This repo includes two MCP paths:

- `mcp_graduation_server/` — existing HTTP JSON-RPC MCP server for deterministic graduation-audit tools.
- `mcp_server/` — local `stdio` MCP adapter for Cursor, Claude Desktop, and other local MCP clients.

See `mcp_server/README.md` for install, run, and client configuration instructions.

---

## 🔌 API Endpoints (CSE226 Rubric)

The platform strictly exposes the modular audit logic via proper REST API endpoints.

### 1. Level 1 Audit: Credit Tallying
**Endpoint:** `POST /audit/level1`
**Description:** Parses the CSV, resolves retakes, and calculates attempted/earned credits.
**Request (FormData):**
- `file`: `UploadFile` (Transcript CSV)
- `program`: `str` (e.g., "CSE" or "BBA")

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "credits_attempted": 133,
    "credits_earned": 124,
    "unrecognized": []
  }
}
```

### 2. Level 2 Audit: CGPA & Probation
**Endpoint:** `POST /audit/level2`
**Description:** Calculates the cumulative GPA using best-grade logic and evaluates academic standing (Probation/Dismissal phases).
**Request (FormData):**
- `file`: `UploadFile`
- `program`: `str`

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "cgpa": 3.75,
    "quality_points": 487.5,
    "gpa_credits": 124,
    "standing": "NORMAL",
    "probation_count": 0,
    "credit_reduction": 0
  }
}
```

### 3. Level 3 Audit: Graduation Check
**Endpoint:** `POST /audit/level3`
**Description:** Compares the transcript against the specific curriculum (CSE or BBA) to identify missing mandatory courses and outstanding elective requirements.
**Request (FormData):**
- `file`: `UploadFile`
- `program`: `str`

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "eligible": false,
    "missing": ["CSE299", "CSE498R"],
    "counts": {
      "mandatory_required": 73,
      "mandatory_earned": 67
    }
  }
}
```

### 4. Full Unified Audit
**Endpoint:** `POST /audit/full`
**Description:** Runs the complete pipeline and generates a categorized "Path to Graduation" roadmap.
**Request (FormData):**
- `file`: `UploadFile`
- `program`: `str`

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "level_1": {...},
    "level_2": {...},
    "level_3": {...},
    "roadmap": {
      "High": ["ENG105"],
      "Medium": [],
      "Low": []
    }
  }
}
```

---
*Developed for North South University Academic Auditing.*
