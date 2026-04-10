"""
Калькулятор вирусности контента
"""
from datetime import datetime, timezone
from typing import Dict
from config.settings import settings


class ViralCalculator:
    """Класс для расчета метрик вирусности"""

    @staticmethod
    def calculate_engagement_rate(likes: int, comments: int, views: int) -> float:
        """
        Расчет engagement rate

        Formula: (likes + comments) / views
        """
        if views == 0:
            return 0.0

        engagement_rate = (likes + comments) / views
        return round(engagement_rate, 4)

    @staticmethod
    def calculate_viral_score(views: int, likes: int, comments: int) -> float:
        """
        Расчет viral score

        Formula: (views * 0.4) + (likes * 0.3) + (comments * 0.3)
        """
        viral_score = (views * 0.4) + (likes * 0.3) + (comments * 0.3)
        return round(viral_score, 2)

    @staticmethod
    def calculate_growth_score(views: int, publish_date: datetime) -> float:
        """
        Расчет growth score (скорость роста)

        Formula: views / hours_since_post
        """
        now = datetime.now(timezone.utc)

        # Обеспечиваем timezone-aware datetime
        if publish_date.tzinfo is None:
            publish_date = publish_date.replace(tzinfo=timezone.utc)

        time_diff = now - publish_date
        hours_since_post = max(time_diff.total_seconds() / 3600, 0.1)  # Минимум 0.1 часа

        growth_score = views / hours_since_post
        return round(growth_score, 2)

    @staticmethod
    def is_viral(views: int, engagement_rate: float, publish_date: datetime) -> bool:
        """
        Определение, является ли контент вирусным

        Критерии:
        - views > VIRAL_MIN_VIEWS
        - engagement_rate > VIRAL_MIN_ENGAGEMENT_RATE
        - post_age < VIRAL_MAX_POST_AGE_HOURS
        """
        now = datetime.now(timezone.utc)

        if publish_date.tzinfo is None:
            publish_date = publish_date.replace(tzinfo=timezone.utc)

        time_diff = now - publish_date
        hours_since_post = time_diff.total_seconds() / 3600

        return (
                views > settings.VIRAL_MIN_VIEWS and
                engagement_rate > settings.VIRAL_MIN_ENGAGEMENT_RATE and
                hours_since_post < settings.VIRAL_MAX_POST_AGE_HOURS
        )

    @staticmethod
    def calculate_all_metrics(
            views: int,
            likes: int,
            comments: int,
            publish_date: datetime
    ) -> Dict[str, float]:
        """
        Расчет всех метрик сразу

        Returns:
            Dict с ключами: engagement_rate, viral_score, growth_score, is_viral
        """
        engagement_rate = ViralCalculator.calculate_engagement_rate(likes, comments, views)
        viral_score = ViralCalculator.calculate_viral_score(views, likes, comments)
        growth_score = ViralCalculator.calculate_growth_score(views, publish_date)
        is_viral = ViralCalculator.is_viral(views, engagement_rate, publish_date)

        return {
            "engagement_rate": engagement_rate,
            "viral_score": viral_score,
            "growth_score": growth_score,
            "is_viral": is_viral
        }