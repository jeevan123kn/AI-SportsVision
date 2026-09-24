import os
from pathlib import Path


class Settings:
    APP_NAME = os.getenv("APP_NAME", "AI SportsVision")
    APP_ENV = os.getenv("APP_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sportsvision.db")
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))


settings = Settings()
