"""
Application Configuration via Environment Variables
AuthRisk-LR System (NFR-MNT-3)
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Artifact paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    MODEL_PATH: str = os.path.join(BASE_DIR, "artifacts", "model.joblib")
    METADATA_PATH: str = os.path.join(BASE_DIR, "artifacts", "model_metadata.json")

    # Policy threshold settings (REQ-INF-3)
    LOW_RISK_THRESHOLD: float = 0.35
    CRITICAL_RISK_THRESHOLD: float = 0.70


settings = Settings()
