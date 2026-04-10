"""
Зависимости для FastAPI
"""
from app.database.connection import get_db
from app.services.reels_service import ReelsService
from sqlalchemy.orm import Session
from fastapi import Depends


def get_reels_service(db: Session = Depends(get_db)) -> ReelsService:
    """Получить сервис Reels"""
    return ReelsService(db)