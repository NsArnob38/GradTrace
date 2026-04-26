from fastapi import APIRouter, HTTPException, Header, Body
from pydantic import BaseModel
from packages.api.config import get_settings
from packages.api.deps import get_supabase_admin
import jwt as pyjwt
import datetime
import os

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin_token(authorization: str) -> dict:
    settings = get_settings()

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not an admin")

    return payload

class AdminLoginRequest(BaseModel):
    admin_id: str
    password: str

@router.post("/login")
async def admin_login(body: AdminLoginRequest):
    settings = get_settings()
    
    # Parse admins from env: "id1:pass1,id2:pass2"
    admins = {}
    for entry in settings.admin_credentials.split(","):
        if ":" in entry:
            aid, pwd = entry.strip().split(":", 1)
            admins[aid] = pwd
    
    if body.admin_id not in admins or admins[body.admin_id] != body.password:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    token = pyjwt.encode({
        "sub": body.admin_id,
        "role": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }, settings.admin_jwt_secret, algorithm="HS256")
    return {"token": token, "admin_id": body.admin_id}


@router.get("/stats")
async def get_stats(authorization: str = Header(...)):
    _require_admin_token(authorization)
        
    db = get_supabase_admin()
    
    p_res = db.table("profiles").select("id", count="exact").execute()
    total_students = p_res.count if p_res.count else 0
    
    a_res = db.table("audit_results").select("id", count="exact").execute()
    total_audits = a_res.count if a_res.count else 0
    
    today = datetime.datetime.utcnow().date().isoformat()
    t_res = db.table("audit_results").select("id", count="exact").gte("generated_at", today).execute()
    audits_today = t_res.count if t_res.count else 0
    
    l_res = db.table("audit_results").select("user_id, generated_at").order("generated_at", desc=True).limit(1).execute()
    latest_audit = None
    if l_res.data:
        sid = l_res.data[0].get("user_id")
        email = "Unknown"
        if sid:
            prof = db.table("profiles").select("email").eq("id", sid).execute()
            if prof.data:
                email = prof.data[0].get("email")
        
        latest_audit = {
            "email": email,
            "created_at": l_res.data[0].get("generated_at")
        }
    
    return {
        "total_students": total_students,
        "total_audits": total_audits,
        "audits_today": audits_today,
        "latest_audit": latest_audit,
    }


@router.get("/students")  
async def get_students(authorization: str = Header(...)):
    _require_admin_token(authorization)
         
    db = get_supabase_admin()
    profiles = db.table("profiles").select(
        "id, email, created_at, role, full_name, student_id, program, bba_concentration"
    ).order("created_at", desc=True).execute()
    students = profiles.data or []
    
    for s in students:
        hist = db.table("audit_results").select("id", count="exact").eq("user_id", s["id"]).execute()
        s["total_audits"] = hist.count if hist.count else 0

        latest = db.table("scan_history") \
            .select("summary, scanned_at") \
            .eq("user_id", s["id"]) \
            .order("scanned_at", desc=True) \
            .limit(1) \
            .execute()
        s["latest_audit"] = latest.data[0] if latest.data else None
         
    return students


@router.get("/students/{student_id}")
async def get_student_detail(student_id: str, authorization: str = Header(...)):
    _require_admin_token(authorization)

    db = get_supabase_admin()

    profile = db.table("profiles") \
        .select("*") \
        .eq("id", student_id) \
        .single() \
        .execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Student not found")

    history = db.table("scan_history") \
        .select("*") \
        .eq("user_id", student_id) \
        .order("scanned_at", desc=True) \
        .execute()

    latest_audit = None
    if history.data:
        latest_audit_id = history.data[0].get("audit_result_id")
        if latest_audit_id:
            latest = db.table("audit_results") \
                .select("*") \
                .eq("id", latest_audit_id) \
                .single() \
                .execute()
            latest_audit = latest.data

    return {
        "profile": profile.data,
        "history": history.data or [],
        "latest_audit": latest_audit,
    }


@router.get("/audits")
async def get_audits(authorization: str = Header(...)):
    _require_admin_token(authorization)
        
    db = get_supabase_admin()
    audits = db.table("audit_results").select("*").order("generated_at", desc=True).limit(100).execute()
    results = audits.data or []
    
    for r in results:
        sid = r.get("user_id")
        if sid:
            prof = db.table("profiles").select("email").eq("id", sid).execute()
            r["email"] = prof.data[0].get("email") if prof.data else "Unknown"
        else:
            r["email"] = "Unknown"
            
    return results


@router.get("/admins")
async def list_admins(authorization: str = Header(...)):
    _require_admin_token(authorization)

    settings = get_settings()
    admins = []
    if settings.admin_credentials:
        for entry in settings.admin_credentials.split(","):
            if ":" in entry:
                aid, _ = entry.strip().split(":", 1)
                admins.append(aid)
    return admins


class AddAdminRequest(BaseModel):
    admin_id: str
    password: str


class ProgramEntry(BaseModel):
    program_code: str
    course_code: str
    course_name: str
    credits: int | float
    category: str

@router.post("/admins")
async def add_admin(body: AddAdminRequest, authorization: str = Header(...)):
    settings = get_settings()
    _require_admin_token(authorization)
        
    admins = {}
    if settings.admin_credentials:
        for entry in settings.admin_credentials.split(","):
            if ":" in entry:
                aid, pwd = entry.strip().split(":", 1)
                admins[aid] = pwd
                
    if body.admin_id in admins:
        raise HTTPException(status_code=400, detail="Admin ID already exists")
    
    new_entry = f"{body.admin_id}:{body.password}"
    if settings.admin_credentials:
        new_creds = settings.admin_credentials + "," + new_entry
    else:
        new_creds = new_entry
        
    os.environ["ADMIN_CREDENTIALS"] = new_creds
    return {"success": True}


@router.delete("/admins/{admin_id}")
async def remove_admin(admin_id: str, authorization: str = Header(...)):
    settings = get_settings()
    _require_admin_token(authorization)
        
    admins = []
    if settings.admin_credentials:
        for entry in settings.admin_credentials.split(","):
            if ":" in entry:
                aid, pwd = entry.strip().split(":", 1)
                if aid != admin_id:
                    admins.append(entry.strip())
                
    os.environ["ADMIN_CREDENTIALS"] = ",".join(admins)
    return {"success": True}


@router.get("/programs")
async def list_programs(authorization: str = Header(...)):
    _require_admin_token(authorization)

    db = get_supabase_admin()
    result = db.table("programs").select("*").execute()
    return result.data or []


@router.put("/programs")
async def update_programs(entries: list[ProgramEntry] = Body(...), authorization: str = Header(...)):
    _require_admin_token(authorization)

    db = get_supabase_admin()
    payload = [entry.model_dump() for entry in entries]

    if payload:
        program_codes = sorted({entry["program_code"] for entry in payload})
        for program_code in program_codes:
            db.table("programs").delete().eq("program_code", program_code).execute()
        db.table("programs").insert(payload).execute()

    return {"updated": len(payload)}


@router.delete("/programs/{program_code}")
async def delete_program(program_code: str, authorization: str = Header(...)):
    _require_admin_token(authorization)

    normalized = program_code.strip().upper()
    if not normalized:
        raise HTTPException(status_code=400, detail="Program code is required")

    db = get_supabase_admin()
    db.table("programs").delete().eq("program_code", normalized).execute()
    return {"deleted": True, "program_code": normalized}
