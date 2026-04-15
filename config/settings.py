"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/viral_reels"

    # Instagram
    INSTAGRAM_USERNAME: str = ""  # Оставляем пустым!
    INSTAGRAM_PASSWORD: str = ""  # Оставляем пустым!
    # RapidAPI
    RAPIDAPI_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # Scraping
    SCRAPE_DELAY_MIN: float = 3.0  # Минимум 3 секунды
    SCRAPE_DELAY_MAX: float = 7.0  # Максимум 7 секунд
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    USE_PROXY: bool = False
    PROXY_URL: Optional[str] = None

    # Viral thresholds
    VIRAL_MIN_VIEWS: int = 10000
    VIRAL_MIN_ENGAGEMENT_RATE: float = 0.05
    VIRAL_MAX_POST_AGE_HOURS: int = 72

    # Scheduler
    COLLECT_INTERVAL_MINUTES: int = 30
    UPDATE_METRICS_INTERVAL_HOURS: int = 2
    RECALCULATE_SCORES_INTERVAL_HOURS: int = 24

    # Dashboard
    DASHBOARD_PORT: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()