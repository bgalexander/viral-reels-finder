"""
Модели базы данных
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Reel(Base):
    """Модель для хранения данных о Reels"""

    __tablename__ = "reels"

    id = Column(Integer, primary_key=True, index=True)
    reel_id = Column(String(255), unique=True, index=True, nullable=False)
    url = Column(String(500), nullable=False)
    video_url = Column(String(500), nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)  # Список хэштегов
    audio_name = Column(String(500), nullable=True)
    publish_date = Column(DateTime, nullable=False)

    # Метрики
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    duration = Column(Float, nullable=True)  # в секундах

    # Аналитика
    engagement_rate = Column(Float, default=0.0)
    viral_score = Column(Float, default=0.0)
    growth_score = Column(Float, default=0.0)
    is_viral = Column(Boolean, default=False)

    # Метаданные
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_scraped_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Reel {self.reel_id} - Score: {self.viral_score}>"


class Source(Base):
    """Модель для хранения источников парсинга"""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False)  # 'hashtag' или 'account'
    name = Column(String(255), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime, nullable=True)
    total_reels_collected = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Source {self.source_type}:{self.name}>"


class ScrapingLog(Base):
    """Логи парсинга"""

    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey('sources.id'))
    status = Column(String(50), nullable=False)  # 'success', 'failed', 'partial'
    reels_collected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<ScrapingLog {self.status} - {self.reels_collected} reels>"