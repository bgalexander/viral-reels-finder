"""
Публичный парсер Instagram БЕЗ авторизации
Использует официальный публичный API
"""
import requests
import json
import time
import random
from typing import List, Dict, Optional
from datetime import datetime, timezone
import logging
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstagramPublicScraper:
    """Парсер публичных данных Instagram без авторизации"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-IG-App-ID': '936619743392459',  # Публичный App ID Instagram
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com'
        })

        # Получаем CSRF token
        self._init_session()

    def _init_session(self):
        """Инициализация сессии и получение cookies"""
        try:
            response = self.session.get('https://www.instagram.com/', timeout=10)
            # Извлекаем CSRF token из cookies
            csrf_token = response.cookies.get('csrftoken')
            if csrf_token:
                self.session.headers['X-CSRFToken'] = csrf_token
                logger.info("✅ Сессия инициализирована")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации сессии: {e}")

    def _random_delay(self):
        """Случайная задержка между запросами"""
        delay = random.uniform(
            settings.SCRAPE_DELAY_MIN,
            settings.SCRAPE_DELAY_MAX
        )
        logger.debug(f"⏳ Задержка {delay:.1f} сек...")
        time.sleep(delay)

    def get_post_by_shortcode(self, shortcode: str) -> Optional[Dict]:
        """
        Получить публичные данные поста по shortcode

        Args:
            shortcode: Короткий код поста (из URL)

        Returns:
            Словарь с данными поста или None
        """
        url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"

        try:
            self._random_delay()

            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()

                if 'items' in data and len(data['items']) > 0:
                    post = data['items'][0]
                    return self._extract_post_data(post)

            logger.warning(f"⚠️ Не удалось получить данные для {shortcode}")
            return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения поста {shortcode}: {e}")
            return None

    def _extract_post_data(self, post: Dict) -> Optional[Dict]:
        """Извлечь данные из JSON поста"""
        try:
            # Проверяем что это видео (Reel)
            if not post.get('video_url'):
                return None

            # Извлечение хэштегов из caption
            caption = post.get('caption', {}).get('text', '')
            hashtags = []
            if caption:
                words = caption.split()
                hashtags = [
                    word.strip('#').lower()
                    for word in words
                    if word.startswith('#')
                ]

            # Формирование данных
            reel_data = {
                'reel_id': post.get('code'),
                'url': f"https://www.instagram.com/reel/{post.get('code')}/",
                'video_url': post.get('video_url'),
                'caption': caption,
                'hashtags': hashtags[:10],
                'audio_name': None,
                'publish_date': datetime.fromtimestamp(
                    post.get('taken_at', 0),
                    tz=timezone.utc
                ),
                'views': post.get('play_count', 0),
                'likes': post.get('like_count', 0),
                'comments': post.get('comment_count', 0),
                'duration': post.get('video_duration')
            }

            return reel_data

        except Exception as e:
            logger.error(f"❌ Ошибка извлечения данных: {e}")
            return None

    def collect_trending_reels(self, limit: int = 20) -> List[Dict]:
        """
        Собрать трендовые Reels из публичного Explore

        ВНИМАНИЕ: Этот метод может не работать без авторизации
        Используйте для демонстрации с заранее известными shortcodes

        Args:
            limit: Количество Reels

        Returns:
            Список словарей с данными Reels
        """
        logger.warning("⚠️ Сбор трендовых Reels без авторизации ограничен")
        logger.info("💡 Рекомендуется использовать API с прямыми ссылками на Reels")

        # Можно вернуть заранее известные популярные Reels
        # или интегрироваться с другими API

        return []


def collect_reels_by_urls(urls: List[str]) -> List[Dict]:
    """
    Собрать данные Reels по списку URL

    Args:
        urls: Список URL вида https://www.instagram.com/reel/ABC123/

    Returns:
        Список словарей с данными Reels
    """
    scraper = InstagramPublicScraper()
    reels = []

    for url in urls:
        # Извлекаем shortcode из URL
        parts = url.rstrip('/').split('/')
        if 'reel' in parts or 'p' in parts:
            shortcode = parts[-1]

            logger.info(f"📥 Сбор данных для {shortcode}...")
            reel_data = scraper.get_post_by_shortcode(shortcode)

            if reel_data:
                reels.append(reel_data)
                logger.info(f"   ✅ Получено - Views: {reel_data['views']:,}")
            else:
                logger.warning(f"   ❌ Не удалось получить данные")

    return reels