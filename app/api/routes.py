"""
API маршруты
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.services.reels_service import ReelsService
from app.api.dependencies import get_reels_service

router = APIRouter()


# Pydantic модели для API


class ReelResponse(BaseModel):
    """Модель ответа для Reel"""
    id: int
    reel_id: str
    url: str
    video_url: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    audio_name: Optional[str] = None
    publish_date: datetime
    views: int
    likes: int
    comments: int
    duration: Optional[float] = None
    engagement_rate: float
    viral_score: float
    growth_score: float
    is_viral: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    """Модель ответа для Source"""
    id: int
    source_type: str
    name: str
    is_active: bool
    last_scraped_at: Optional[datetime] = None
    total_reels_collected: int
    created_at: datetime

    class Config:
        from_attributes = True


class SourceCreate(BaseModel):
    """Модель для создания источника"""
    source_type: str = Field(..., description="Тип источника: 'hashtag' или 'account'")
    name: str = Field(..., description="Название хэштега или username")


class StatsResponse(BaseModel):
    """Модель ответа со статистикой"""
    total_reels: int
    viral_reels: int
    total_views: int
    total_likes: int
    total_comments: int
    avg_engagement_rate: float


# API эндпоинты


@router.get("/", tags=["General"])
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Viral Reels Finder API",
        "version": "1.0.0",
        "status": "running"
    }


@router.get("/viral", response_model=List[ReelResponse], tags=["Reels"])
async def get_viral_reels(
        limit: int = Query(50, ge=1, le=100, description="Количество результатов"),
        skip: int = Query(0, ge=0, description="Пропустить N записей"),
        service: ReelsService = Depends(get_reels_service)
):
    """
    Получить топ вирусных Reels

    Возвращает список Reels, отсортированных по viral_score (по убыванию)
    """
    reels = service.get_viral_reels(limit=limit, skip=skip)
    return reels


@router.get("/trending", response_model=List[ReelResponse], tags=["Reels"])
async def get_trending_reels(
        limit: int = Query(50, ge=1, le=100, description="Количество результатов"),
        skip: int = Query(0, ge=0, description="Пропустить N записей"),
        service: ReelsService = Depends(get_reels_service)
):
    """
    Получить быстрорастущие Reels

    Возвращает список Reels с наибольшим growth_score (просмотры/час)
    """
    reels = service.get_trending_reels(limit=limit, skip=skip)
    return reels


@router.get("/reels/{reel_id}", response_model=ReelResponse, tags=["Reels"])
async def get_reel(
        reel_id: str,
        service: ReelsService = Depends(get_reels_service)
):
    """
    Получить детальную информацию о конкретном Reel

    Args:
        reel_id: Уникальный ID Reel (shortcode из Instagram)
    """
    reel = service.get_reel_by_id(reel_id)
    if not reel:
        raise HTTPException(status_code=404, detail="Reel не найден")
    return reel


@router.get("/hashtags/{name}", response_model=List[ReelResponse], tags=["Hashtags"])
async def get_reels_by_hashtag(
        name: str,
        limit: int = Query(50, ge=1, le=100, description="Количество результатов"),
        service: ReelsService = Depends(get_reels_service)
):
    """
    Получить вирусные Reels по конкретному хэштегу

    Args:
        name: Название хэштега (без символа #)
    """
    reels = service.get_reels_by_hashtag(name, limit=limit)
    return reels


@router.get("/sources", response_model=List[SourceResponse], tags=["Sources"])
async def get_sources(
        service: ReelsService = Depends(get_reels_service)
):
    """
    Получить список всех источников парсинга
    """
    sources = service.get_all_sources()
    return sources


@router.post("/sources", response_model=SourceResponse, tags=["Sources"])
async def create_source(
        source: SourceCreate,
        service: ReelsService = Depends(get_reels_service)
):
    """
    Добавить новый источник для парсинга

    Args:
        source: Данные источника (type: 'hashtag' или 'account', name: название)
    """
    if source.source_type not in ['hashtag', 'account']:
        raise HTTPException(
            status_code=400,
            detail="source_type должен быть 'hashtag' или 'account'"
        )

    new_source = service.add_source(source.source_type, source.name)
    return new_source


@router.post("/sources/{source_id}/toggle", response_model=SourceResponse, tags=["Sources"])
async def toggle_source(
        source_id: int,
        service: ReelsService = Depends(get_reels_service)
):
    """
    Включить/выключить источник

    Args:
        source_id: ID источника
    """
    source = service.toggle_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    return source


@router.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_statistics(
        service: ReelsService = Depends(get_reels_service)
):
    """
    Получить общую статистику по базе данных
    """
    from sqlalchemy import func
    from app.models.models import Reel

    db = service.db

    total_reels = db.query(func.count(Reel.id)).scalar()
    viral_reels = db.query(func.count(Reel.id)).filter(Reel.is_viral == True).scalar()

    stats = db.query(
        func.sum(Reel.views).label('total_views'),
        func.sum(Reel.likes).label('total_likes'),
        func.sum(Reel.comments).label('total_comments'),
        func.avg(Reel.engagement_rate).label('avg_engagement_rate')
    ).first()

    return {
        "total_reels": total_reels or 0,
        "viral_reels": viral_reels or 0,
        "total_views": int(stats.total_views or 0),
        "total_likes": int(stats.total_likes or 0),
        "total_comments": int(stats.total_comments or 0),
        "avg_engagement_rate": float(stats.avg_engagement_rate or 0)
    }


@router.post("/collect/trigger", tags=["Management"])
async def trigger_collection(
        service: ReelsService = Depends(get_reels_service)
):
    """
    Вручную запустить сбор Reels из источников

    Внимание: эта операция может занять продолжительное время
    """
    try:
        service.collect_reels_from_sources()
        return {"status": "success", "message": "Сбор данных завершен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сбора: {str(e)}")


@router.post("/metrics/update", tags=["Management"])
async def trigger_metrics_update(
        service: ReelsService = Depends(get_reels_service)
):
    """
    Вручную запустить обновление метрик
    """
    try:
        service.update_metrics()
        return {"status": "success", "message": "Метрики обновлены"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления: {str(e)}")