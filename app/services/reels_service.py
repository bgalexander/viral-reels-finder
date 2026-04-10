"""
Сервис для работы с Reels
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.models.models import Reel, Source, ScrapingLog
from app.collectors.instagram_collector import InstagramCollector
from app.analytics.viral_calculator import ViralCalculator
import logging

logger = logging.getLogger(__name__)


class ReelsService:
    """Сервис для управления Reels"""

    def __init__(self, db: Session):
        self.db = db
        self.collector = InstagramCollector()
        self.calculator = ViralCalculator()

    def get_viral_reels(self, limit: int = 50, skip: int = 0) -> List[Reel]:
        """Получить топ вирусных Reels"""
        return (
            self.db.query(Reel)
            .filter(Reel.is_viral == True)
            .order_by(desc(Reel.viral_score))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_trending_reels(self, limit: int = 50, skip: int = 0) -> List[Reel]:
        """Получить быстрорастущие Reels"""
        return (
            self.db.query(Reel)
            .order_by(desc(Reel.growth_score))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_reel_by_id(self, reel_id: str) -> Optional[Reel]:
        """Получить Reel по ID"""
        return self.db.query(Reel).filter(Reel.reel_id == reel_id).first()

    def get_reels_by_hashtag(self, hashtag: str, limit: int = 50) -> List[Reel]:
        """Получить Reels по хэштегу"""
        return (
            self.db.query(Reel)
            .filter(Reel.hashtags.contains([hashtag]))
            .order_by(desc(Reel.viral_score))
            .limit(limit)
            .all()
        )

    def create_or_update_reel(self, reel_data: dict) -> Reel:
        """
        Создать или обновить Reel

        Args:
            reel_data: Словарь с данными Reel

        Returns:
            Объект Reel
        """
        # Проверяем, существует ли Reel
        existing_reel = self.get_reel_by_id(reel_data['reel_id'])

        # Рассчитываем метрики
        metrics = self.calculator.calculate_all_metrics(
            views=reel_data['views'],
            likes=reel_data['likes'],
            comments=reel_data['comments'],
            publish_date=reel_data['publish_date']
        )

        if existing_reel:
            # Обновляем существующий
            for key, value in reel_data.items():
                setattr(existing_reel, key, value)

            existing_reel.engagement_rate = metrics['engagement_rate']
            existing_reel.viral_score = metrics['viral_score']
            existing_reel.growth_score = metrics['growth_score']
            existing_reel.is_viral = metrics['is_viral']
            existing_reel.last_scraped_at = datetime.now(timezone.utc)

            reel = existing_reel
        else:
            # Создаем новый
            reel = Reel(
                **reel_data,
                engagement_rate=metrics['engagement_rate'],
                viral_score=metrics['viral_score'],
                growth_score=metrics['growth_score'],
                is_viral=metrics['is_viral']
            )
            self.db.add(reel)

        self.db.commit()
        self.db.refresh(reel)

        return reel

    def collect_reels_from_sources(self):
        """Собрать Reels из всех активных источников"""
        sources = self.db.query(Source).filter(Source.is_active == True).all()

        logger.info(f"📥 Начинаем сбор из {len(sources)} источников")

        for source in sources:
            start_time = datetime.now()
            reels_collected = 0
            status = 'success'
            error_message = None

            try:
                if source.source_type == 'hashtag':
                    reels_data = self.collector.collect_from_hashtag(source.name, limit=50)
                elif source.source_type == 'account':
                    reels_data = self.collector.collect_from_account(source.name, limit=50)
                else:
                    continue

                # Сохраняем собранные Reels
                for reel_data in reels_data:
                    self.create_or_update_reel(reel_data)
                    reels_collected += 1

                # Обновляем информацию об источнике
                source.last_scraped_at = datetime.now(timezone.utc)
                source.total_reels_collected += reels_collected

            except Exception as e:
                status = 'failed'
                error_message = str(e)
                logger.error(f"❌ Ошибка сбора из {source.name}: {e}")

            # Логируем результат
            duration = (datetime.now() - start_time).total_seconds()
            log = ScrapingLog(
                source_id=source.id,
                status=status,
                reels_collected=reels_collected,
                error_message=error_message,
                duration_seconds=duration
            )
            self.db.add(log)
            self.db.commit()

        logger.info("✅ Сбор завершен")

    def update_metrics(self):
        """Обновить метрики для всех Reels"""
        logger.info("🔄 Обновление метрик...")

        # Обновляем только недавние Reels (последние 7 дней)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        reels = self.db.query(Reel).filter(Reel.publish_date >= week_ago).all()

        updated_count = 0
        for reel in reels:
            try:
                # Здесь можно добавить реальное обновление метрик через API
                # Пока пересчитываем на основе существующих данных
                metrics = self.calculator.calculate_all_metrics(
                    views=reel.views,
                    likes=reel.likes,
                    comments=reel.comments,
                    publish_date=reel.publish_date
                )

                reel.engagement_rate = metrics['engagement_rate']
                reel.viral_score = metrics['viral_score']
                reel.growth_score = metrics['growth_score']
                reel.is_viral = metrics['is_viral']

                updated_count += 1

            except Exception as e:
                logger.error(f"Ошибка обновления Reel {reel.reel_id}: {e}")

        self.db.commit()
        logger.info(f"✅ Обновлено {updated_count} Reels")

    def recalculate_scores(self):
        """Пересчитать оценки вирусности для всех Reels"""
        logger.info("🔄 Пересчет оценок вирусности...")

        reels = self.db.query(Reel).all()

        for reel in reels:
            metrics = self.calculator.calculate_all_metrics(
                views=reel.views,
                likes=reel.likes,
                comments=reel.comments,
                publish_date=reel.publish_date
            )

            reel.engagement_rate = metrics['engagement_rate']
            reel.viral_score = metrics['viral_score']
            reel.growth_score = metrics['growth_score']
            reel.is_viral = metrics['is_viral']

        self.db.commit()
        logger.info(f"✅ Пересчитаны оценки для {len(reels)} Reels")

    # Методы для управления источниками

    def add_source(self, source_type: str, name: str) -> Source:
        """Добавить новый источник"""
        existing = self.db.query(Source).filter(Source.name == name).first()

        if existing:
            logger.info(f"Источник {name} уже существует")
            return existing

        source = Source(source_type=source_type, name=name)
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        logger.info(f"✅ Добавлен источник: {source_type}:{name}")
        return source

    def get_all_sources(self) -> List[Source]:
        """Получить все источники"""
        return self.db.query(Source).all()

    def toggle_source(self, source_id: int) -> Source:
        """Включить/выключить источник"""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if source:
            source.is_active = not source.is_active
            self.db.commit()
            self.db.refresh(source)
        return source