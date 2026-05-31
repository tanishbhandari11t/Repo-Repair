"""Configuration management for RepoRepair."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GitHub Configuration
    github_token: Optional[str] = None
    
    # Gemini Configuration
    gemini_api_key: Optional[str] = None
    gemini_planning_model: str = "gemini-2.5-flash"
    gemini_coding_model: str = "gemini-2.5-flash"
    
    # Groq Configuration
    groq_api_key: Optional[str] = None
    groq_planning_model: str = "llama-3.3-70b-specdec"
    groq_coding_model: str = "llama-3.3-70b-specdec"
    
    # Workspace Configuration
    workspace_dir: Path = Path("./workspace")
    max_diff_lines: int = 300
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "reporepair.log"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
