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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days (7 * 24 * 60)

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

    # Cloudinary (for file uploads - legacy)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    CLOUDINARY_FOLDER: str = "BDD_CLOUDINARY"  # Default folder for organization

    # Alibaba Cloud OSS (primary file storage)
    # Use internal endpoint (oss-ap-southeast-6-internal.aliyuncs.com) when on Alibaba Cloud ECS
    # Use public endpoint (oss-ap-southeast-6.aliyuncs.com) for local development
    OSS_ACCESS_KEY_ID: Optional[str] = None
    OSS_ACCESS_KEY_SECRET: Optional[str] = None
    OSS_BUCKET_NAME: str = "bdd-oss-goli"
    OSS_ENDPOINT: str = "oss-ap-southeast-6.aliyuncs.com"
    OSS_REGION: str = "ap-southeast-6"

    # Google Services (optional)
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    GOOGLE_GEMINI_API_KEY: Optional[str] = None

    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Resend Email Service
    RESEND_API_KEY: Optional[str] = None
    NOTIFICATION_EMAIL: Optional[str] = None
    RESEND_TEMPLATE_ID: Optional[str] = None
    FRONTEND_URL: str = "https://bdd.hotelsogo-ai.com"

    # Project info
    PROJECT_NAME: str = "BDD Property Tracker"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()