# app/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/loan_db",
        description="PostgreSQL database URL"
    )
    
    # API Settings
    api_v1_str: str = "/api/v1"
    project_name: str = "Loan Approval System"
    version: str = "1.0.0"
    debug: bool = Field(default=False, description="Debug mode")
    
    # ML Settings - FIXED: renamed from model_path to ml_model_path
    ml_model_path: str = Field(default="data/models/loan_model.pkl")
    preprocessor_path: str = Field(default="data/models/preprocessor.pkl")
    
    # LLM Settings - FIXED: renamed from llm_model to llm_model_name
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    llm_model_name: str = Field(default="gpt-4", description="LLM model name")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here")
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    
    # Pydantic v2 configuration
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ('settings_',),
        "extra": "ignore"  # This will ignore extra fields instead of raising errors
    }

settings = Settings()