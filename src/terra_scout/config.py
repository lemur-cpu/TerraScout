from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TERRASCOUT_",
        env_file=".env",
        extra="ignore",
    )

    cache_dir: Path = Path("./data/cache")
    database_path: Path = Path("./var/terra_scout.sqlite3")
    output_dir: Path = Path("./output")
    max_download_megabytes: float = 50.0
    max_llm_tokens: int = 8000
    max_agent_iterations: int = 8
    max_parallel_jobs: int = 2
    max_spend_usd: float = 0.0
    send_precise_coordinates_to_llm: bool = False
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8501

    opentopography_api_key: str = ""
    ollama_host: str = ""


def get_settings() -> Settings:
    return Settings()
