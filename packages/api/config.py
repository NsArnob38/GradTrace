"""
GradeTrace API — Configuration

Loads environment variables for Supabase connection and API settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:19000"

    # Domain restriction
    allowed_email_domain: str = "northsouth.edu"

    # Admin Auth
    admin_credentials: str = ""  # format: "id1:pass1,id2:pass2"
    admin_jwt_secret: str = "change-this-secret"

    # Google Cloud Vision (OCR) - Legacy
    google_credentials_json: str = ""  # The raw JSON content from Service Account Key file
    
    # Gemini 1.5 Flash (LLM Parser)
    gemini_api_key: str = ""
    advisor_model: str = "gemini-3.1-flash-lite-preview"

    # Graduation MCP
    mcp_server_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
