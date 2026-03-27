"""
GradeTrace API — Auth Routes

Supports Google OAuth (via Supabase frontend) and email/password auth for CLI/mobile.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from packages.api.deps import get_current_user, get_supabase_admin, success_response
from packages.api.config import get_settings

router = APIRouter(tags=["auth"])


@router.get("/me")
async def get_profile(user: dict = Depends(get_current_user)):
    """Returns current user's profile."""
    db = get_supabase_admin()
    result = db.table("profiles").select("*").eq("id", user["id"]).single().execute()
    return success_response(result.data)


@router.put("/me")
async def update_profile(updates: dict, user: dict = Depends(get_current_user)):
    """Update current user's profile (program, concentration, etc.)."""
    allowed = {"full_name", "student_id", "program", "bba_concentration"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        return success_response(None)

    db = get_supabase_admin()
    result = db.table("profiles").update(filtered).eq("id", user["id"]).execute()
    return success_response(result.data[0] if result.data else None)


@router.post("/auth/login")
async def login(
    email: str = Body(...),
    password: str = Body(...),
):
    """Authenticate via email + password. Returns Supabase JWT tokens."""
    settings = get_settings()

    # Domain restriction
    if settings.allowed_email_domain:
        if not email.endswith(f"@{settings.allowed_email_domain}"):
            raise HTTPException(
                status_code=403,
                detail=f"Only @{settings.allowed_email_domain} emails are allowed",
            )

    from supabase import create_client
    client = create_client(settings.supabase_url, settings.supabase_anon_key)

    try:
        result = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

    if not result.session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return success_response({
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "expires_in": result.session.expires_in,
        "user": {
            "id": result.user.id,
            "email": result.user.email,
        },
    })


@router.post("/auth/register")
async def register(
    email: str = Body(...),
    password: str = Body(...),
    full_name: str = Body(default=""),
    student_id: str = Body(default=""),
):
    """Register a new user OR set a password for an existing Google OAuth user."""
    settings = get_settings()

    # Domain restriction
    if settings.allowed_email_domain:
        if not email.endswith(f"@{settings.allowed_email_domain}"):
            raise HTTPException(
                status_code=403,
                detail=f"Only @{settings.allowed_email_domain} emails are allowed",
            )

    admin_db = get_supabase_admin()

    # Check if user already exists in profiles
    profile_res = admin_db.table("profiles").select("id").eq("email", email).execute()
    
    if profile_res.data:
        # User exists (likely via Google OAuth). Just set their password!
        user_id = profile_res.data[0]["id"]
        try:
            admin_db.auth.admin.update_user_by_id(user_id, {"password": password})
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to set password: {str(e)}")
            
        return success_response({
            "user_id": user_id,
            "email": email,
            "message": "Password linked to your existing account. You can now log in.",
        })

    # User does not exist, create a new account
    from supabase import create_client
    client = create_client(settings.supabase_url, settings.supabase_anon_key)

    try:
        result = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "student_id": student_id,
                },
            },
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

    if not result.user:
        raise HTTPException(status_code=400, detail="Registration failed")

    return success_response({
        "user_id": result.user.id,
        "email": result.user.email,
        "message": "Account created. You can now log in.",
    })


@router.post("/auth/refresh")
async def refresh_token(
    refresh_token: str = Body(...),
):
    """Refresh an expired access token."""
    settings = get_settings()
    from supabase import create_client
    client = create_client(settings.supabase_url, settings.supabase_anon_key)

    try:
        result = client.auth.refresh_session(refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

    if not result.session:
        raise HTTPException(status_code=401, detail="Could not refresh session")

    return success_response({
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "expires_in": result.session.expires_in,
    })


@router.post("/auth/otp/send")
async def send_otp(email: str = Body(...)):
    """Send a 6-digit OTP code to the user's email."""
    settings = get_settings()

    if settings.allowed_email_domain and not email.endswith(f"@{settings.allowed_email_domain}"):
        raise HTTPException(status_code=403, detail="Invalid email domain")

    from supabase import create_client
    client = create_client(settings.supabase_url, settings.supabase_anon_key)

    try:
        # Request a 6-digit OTP instead of a magic link
        client.auth.sign_in_with_otp({
            "email": email,
            "options": {"should_create_user": False}
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send code: {str(e)}")

    return success_response({"message": "OTP sent successfully"})


@router.post("/auth/otp/verify")
async def verify_otp(
    email: str = Body(...),
    token: str = Body(...)
):
    """Verify the 6-digit OTP and return a session."""
    settings = get_settings()
    from supabase import create_client
    client = create_client(settings.supabase_url, settings.supabase_anon_key)

    try:
        result = client.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "magiclink"
        })
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Verification failed: {str(e)}")

    if not result.session:
        raise HTTPException(status_code=401, detail="Invalid or expired code")

    return success_response({
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
        "expires_in": result.session.expires_in,
        "user": {
            "id": result.user.id,
            "email": result.user.email,
        },
    })
