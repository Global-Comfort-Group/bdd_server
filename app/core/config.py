from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: Optional[str] = None

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str) -> str:
        if isinstance(v, str):
            return v
        return ""

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        if not self.ALLOWED_ORIGINS.strip():
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIRECTORY: str = "./uploads"

    # Cloudinary (for file uploads)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    CLOUDINARY_FOLDER: str = "BDD_CLOUDINARY"  # Default folder for organization

    # Google Services (optional)
    GOOGLE_MAPS_API_KEY: Optional[str] = None

    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Project info
    PROJECT_NAME: str = "BDD Property Tracker"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()