from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Finance Tracking API"
    app_version: str = "1.0.0"
    debug: bool = False
    app_port: int = 8000
    
    # Supabase settings
    # Set these via environment (.env) in production. Avoid hard-coding secrets here.
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_project_id: str = ""
    
    # JWT settings
    # JWT secret - set in environment
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    allowed_origins: list = ["*"]
    allowed_methods: list = ["*"]
    allowed_headers: list = ["*"]
    
    class Config:
        env_file = ".env"
    # Optionally expose other service API keys via settings (e.g., Z.ai)
    zai_api_key: Optional[str] = None


settings = Settings()