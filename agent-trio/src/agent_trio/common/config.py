"""Centralized configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("AGENT_MODEL", "gpt-4.1-mini")
    model_strong: str = os.getenv("AGENT_MODEL_STRONG", "gpt-4.1")

    # Trading
    alpha_vantage_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    polygon_key: str = os.getenv("POLYGON_API_KEY", "")
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")

    # Second brain
    notion_api_key: str = os.getenv("NOTION_API_KEY", "")
    notion_tasks_db: str = os.getenv("NOTION_TASKS_DB_ID", "")
    notion_notes_db: str = os.getenv("NOTION_NOTES_DB_ID", "")

    # Research
    semantic_scholar_key: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8080"))
    api_auth_token: str = os.getenv("API_AUTH_TOKEN", "change-me")


settings = Settings()
