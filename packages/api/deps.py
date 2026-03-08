"""
GradeTrace API — Dependencies

Supabase clients and authentication helpers.
"""

from fastapi import Depends, HTTPException, Header
from supabase import create_client, Client
from functools import lru_cache

from packages.api.config import get_settings, Settings
import httpx

# --- HTTP/2 Monkeypatch for Windows ---
# Supabase Python client frequently drops HTTP/2 connections on Windows,
# resulting in 'RemoteProtocolError: ConnectionTerminated'.
# Forcing httpx to use HTTP/1.1 resolves this entirely.
_original_client_init = httpx.Client.__init__
_original_async_client_init = httpx.AsyncClient.__init__

def _patched_client_init(self, *args, **kwargs):
    kwargs["http2"] = False
    _original_client_init(self, *args, **kwargs)

def _patched_async_client_init(self, *args, **kwargs):
    kwargs["http2"] = False
    _original_async_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_client_init
httpx.AsyncClient.__init__ = _patched_async_client_init
# --------------------------------------

# ───────────────────────────────────────────────
# Supabase Clients
# ───────────────────────────────────────────────

@lru_cache()
def get_supabase_admin() -> Client:
    """Supabase client with service role key (full access, server-side only)."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def get_supabase_client() -> Client:
    """Supabase client with anon key (for RLS-respecting operations)."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_anon_key)


# ───────────────────────────────────────────────
# JWT Authentication (via Supabase server-side)
# ───────────────────────────────────────────────

async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Validate Supabase JWT locally using PyJWT.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    settings = get_settings()

    try:
        import jwt as pyjwt
        print("DEBUG token alg:", pyjwt.get_unverified_header(token))
        payload = pyjwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {"id": user_id, "email": payload.get("email", ""), "role": payload.get("role", "authenticated")}


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    db = get_supabase_admin()
    result = db.table("profiles").select("role").eq("id", user["id"]).single().execute()
    if not result.data or result.data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ───────────────────────────────────────────────
# Response Helpers
# ───────────────────────────────────────────────

def success_response(data=None):
    return {"success": True, "data": data, "error": None}


def error_response(message: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail=message)
