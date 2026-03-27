import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./opportunity_radar.db"
    nse_base_url: str = "https://www.nseindia.com"
    bse_base_url: str = "https://api.bseindia.com/BseIndiaAPI/api"
    scan_interval_minutes: int = 30
    signal_detection_interval_minutes: int = 15
    alert_min_confidence: float = 0.7
    max_alerts_per_day: int = 50

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
