"""
Сборщик данных из Instagram
"""
import instaloader
import time
import random
from typing import List, Dict, Optional
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstagramCollector:
    """Класс для сбора данных Reels из Instagram"""

    def __init__(self):
        self.loader = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            user_agent='Mozilla/5.0'
        )

        self._login()

    def _login(self):
        """Авторизация в Instagram"""
        if settings.INSTAGRAM_USERNAME and settings.INSTAGRAM_PASSWORD:
            try:
                self.loader.login(
                    settings.INSTAGRAM_USERNAME,
                    settings.INSTAGRAM_PASSWORD
                )
                logger.info("✅ Успешная авторизация в Instagram")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка авторизации: {e}")
                logger.info("Продолжаем без авторизации (ограниченный функционал)")

    def _random_delay(self):
        """Случайная задержка между запросами"""
        delay = random.uniform(settings.SCRAPE_DELAY_MIN, settings.SCRAPE_DELAY_MAX)
        time.sleep(delay)

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _safe_request(self, func, *args, **kwargs):
        """Безопасное выполнение запроса с повторными попытками"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            raise

    def _extract_reel_data(self, post) -> Optional[Dict]:
        """
        Извлечение данных из поста

        Returns:
            Dict с данными Reel или None, если это не Reel
        """
        try:
            # Проверяем, что это видео (Reel)
            if not post.is_video:
                return None

            # Извлечение хэштегов
            hashtags = []
            if post.caption:
                hashtags = [tag.strip('#') for tag in post.caption.split() if tag.startswith('#')]

            # Формирование данных
            reel_data = {
                'reel_id': post.shortcode,
                'url': f"https://www.instagram.com/reel/{post.shortcode}/",
                'video_url': post.video_url if hasattr(post, 'video_url') else None,
                'caption': post.caption if post.caption else "",
                'hashtags': hashtags,
                'audio_name': None,  # Instaloader не предоставляет эту информацию напрямую
                'publish_date': post.date_utc.replace(tzinfo=timezone.utc),
                'views': post.video_view_count if hasattr(post, 'video_view_count') else 0,
                'likes': post.likes,
                'comments': post.comments,
                'duration': post.video_duration if hasattr(post, 'video_duration') else None
            }

            return reel_data

        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return None

    def collect_from_hashtag(self, hashtag: str, limit: int = 50) -> List[Dict]:
        """
        Сбор Reels по хэштегу

        Args:
            hashtag: Название хэштега (без #)
            limit: Максимальное количество постов для обработки

        Returns:
            Список словарей с данными Reels
        """
        logger.info(f"🔍 Сбор Reels по хэштегу: #{hashtag}")
        reels = []

        try:
            posts = instaloader.Hashtag.from_name(
                self.loader.context,
                hashtag
            ).get_posts()

            count = 0
            for post in posts:
                if count >= limit:
                    break

                self._random_delay()

                reel_data = self._extract_reel_data(post)
                if reel_data:
                    reels.append(reel_data)
                    logger.info(f"  ✓ Собран Reel: {reel_data['reel_id']}")

                count += 1

            logger.info(f"✅ Собрано {len(reels)} Reels из хэштега #{hashtag}")

        except Exception as e:
            logger.error(f"❌ Ошибка сбора хэштега #{hashtag}: {e}")

        return reels

    def collect_from_account(self, username: str, limit: int = 50) -> List[Dict]:
        """
        Сбор Reels из аккаунта

        Args:
            username: Имя пользователя Instagram
            limit: Максимальное количество постов для обработки

        Returns:
            Список словарей с данными Reels
        """
        logger.info(f"🔍 Сбор Reels из аккаунта: @{username}")
        reels = []

        try:
            profile = instaloader.Profile.from_username(
                self.loader.context,
                username
            )

            posts = profile.get_posts()

            count = 0
            for post in posts:
                if count >= limit:
                    break

                self._random_delay()

                reel_data = self._extract_reel_data(post)
                if reel_data:
                    reels.append(reel_data)
                    logger.info(f"  ✓ Собран Reel: {reel_data['reel_id']}")

                count += 1

            logger.info(f"✅ Собрано {len(reels)} Reels из аккаунта @{username}")

        except Exception as e:
            logger.error(f"❌ Ошибка сбора аккаунта @{username}: {e}")

        return reels