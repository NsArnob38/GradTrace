from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from packages.api.config import get_settings
from packages.api.deps import get_supabase_admin
import jwt as pyjwt
import datetime
import os

router = APIRouter(prefix="/admin", tags=["admin"])

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
    import jwt as pyjwt
    from packages.api.config import get_settings
    settings = get_settings()
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not an admin")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
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
    import jwt as pyjwt
    from packages.api.config import get_settings
    settings = get_settings()
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not an admin")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
    db = get_supabase_admin()
    profiles = db.table("profiles").select("id, email, created_at, role, full_name").order("created_at", desc=True).execute()
    students = profiles.data or []
    
    for s in students:
        hist = db.table("audit_results").select("id", count="exact").eq("user_id", s["id"]).execute()
        s["total_audits"] = hist.count if hist.count else 0
        
    return students


@router.get("/audits")
async def get_audits(authorization: str = Header(...)):
    import jwt as pyjwt
    from packages.api.config import get_settings
    settings = get_settings()
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not an admin")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
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
    import jwt as pyjwt
    from packages.api.config import get_settings
    settings = get_settings()
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not an admin")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
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

@router.post("/admins")
async def add_admin(body: AddAdminRequest, authorization: str = Header(...)):
    import jwt as pyjwt
    from packages.api.config import get_settings
    settings = get_settings()
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not an admin")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
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
    import jwt as pyjwt
    from packages.api.config import get_settings
    settings = get_settings()
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not an admin")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
    admins = []
    if settings.admin_credentials:
        for entry in settings.admin_credentials.split(","):
            if ":" in entry:
                aid, pwd = entry.strip().split(":", 1)
                if aid != admin_id:
                    admins.append(entry.strip())
                
    os.environ["ADMIN_CREDENTIALS"] = ",".join(admins)
    return {"success": True}
