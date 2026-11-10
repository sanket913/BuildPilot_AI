from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_access_token: str = ""
    database_url: str = "sqlite:///./buildpilot.db"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-6-luna"
    ai_timeout_seconds: int = 40
    frontend_origin: str = "http://localhost:5173"
    max_upload_mb: int = 10
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.app_env.lower() == "production" and len(self.app_access_token) < 32:
            raise ValueError("APP_ACCESS_TOKEN must be set to at least 32 characters in production")
        if not 1 <= self.max_upload_mb <= 50:
            raise ValueError("MAX_UPLOAD_MB must be between 1 and 50")
        if not 5 <= self.ai_timeout_seconds <= 120:
            raise ValueError("AI_TIMEOUT_SECONDS must be between 5 and 120")
        return self

settings = Settings()
