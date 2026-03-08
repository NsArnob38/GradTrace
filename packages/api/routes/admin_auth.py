from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from packages.api.config import get_settings
import jwt as pyjwt
import datetime

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
