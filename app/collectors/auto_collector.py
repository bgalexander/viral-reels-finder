"""
Автоматический сбор популярных Reels через RapidAPI
Работает БЕЗ аккаунта Instagram, БЕЗ риска блокировки
"""
import requests
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoReelsCollector:
    """Автоматический сбор Reels через RapidAPI"""

    def __init__(self):
        self.api_key = settings.RAPIDAPI_KEY
        if not self.api_key:
            raise ValueError(
                "❌ RAPIDAPI_KEY не установлен!\n"
                "1. Зарегистрируйтесь на https://rapidapi.com\n"
                "2. Подпишитесь на Instagram Scraper API\n"
                "3. Добавьте RAPIDAPI_KEY в файл .env"
            )

        self.base_url = "https://instagram-scraper-api2.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com"
        }

    def _request(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Выполнить запрос к API"""
        url = f"{self.base_url}/{endpoint}"

        try:
            # Задержка между запросами
            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)

            response = requests.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("⚠️ Лимит запросов. Подождите минуту...")
                time.sleep(60)
                return None
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {e}")
            return None

    def collect_by_hashtag(self, hashtag: str, limit: int = 20) -> List[Dict]:
        """
        Собрать Reels по хэштегу

        Args:
            hashtag: Хэштег без #
            limit: Количество Reels

        Returns:
            Список данных Reels
        """
        logger.info(f"🔍 Поиск Reels по #{hashtag}...")

        data = self._request("v1/hashtag", params={
            "hashtag": hashtag
        })

        if not data:
            return []

        reels = []
        items = data.get('data', {}).get('items', [])

        for item in items[:limit]:
            reel_data = self._extract_reel_data(item)
            if reel_data:
                reels.append(reel_data)

        logger.info(f"✅ Найдено {len(reels)} Reels по #{hashtag}")
        return reels

    def collect_from_profile(self, username: str, limit: int = 20) -> List[Dict]:
        """
        Собрать Reels из публичного профиля

        Args:
            username: Имя пользователя Instagram
            limit: Количество Reels

        Returns:
            Список данных Reels
        """
        logger.info(f"👤 Сбор Reels из профиля @{username}...")

        data = self._request("v1.2/reels", params={
            "username_or_id_or_url": username
        })

        if not data:
            return []

        reels = []
        items = data.get('data', {}).get('items', [])

        for item in items[:limit]:
            reel_data = self._extract_reel_data(item)
            if reel_data:
                reels.append(reel_data)

        logger.info(f"✅ Найдено {len(reels)} Reels от @{username}")
        return reels

    def collect_trending(self, hashtags: List[str] = None, limit: int = 50) -> List[Dict]:
        """
        Собрать трендовые Reels по популярным хэштегам

        Args:
            hashtags: Список хэштегов (если None — используются дефолтные)
            limit: Общий лимит Reels

        Returns:
            Список данных Reels
        """
        if hashtags is None:
            hashtags = [
                "viral", "trending", "reels",
                "explore", "fyp", "funny",
                "travel", "fitness", "food",
                "music", "dance", "fashion",
                "beauty", "comedy", "motivation"
            ]

        logger.info(f"🚀 Сбор трендовых Reels по {len(hashtags)} хэштегам...")

        all_reels = []
        per_hashtag = max(5, limit // len(hashtags))

        for hashtag in hashtags:
            if len(all_reels) >= limit:
                break

            reels = self.collect_by_hashtag(hashtag, limit=per_hashtag)
            all_reels.extend(reels)
            logger.info(f"   #{hashtag}: +{len(reels)} Reels (всего: {len(all_reels)})")

        # Убираем дубликаты
        seen_ids = set()
        unique_reels = []
        for reel in all_reels:
            if reel['reel_id'] not in seen_ids:
                seen_ids.add(reel['reel_id'])
                unique_reels.append(reel)

        logger.info(f"\n📊 Итого: {len(unique_reels)} уникальных Reels")
        return unique_reels[:limit]

    def collect_from_top_profiles(self, limit: int = 50) -> List[Dict]:
        """
        Собрать Reels из популярных профилей

        Args:
            limit: Общий лимит Reels

        Returns:
            Список данных Reels
        """
        # Популярные аккаунты с вирусными Reels
        profiles = [
            "instagram",
            "khaby.lame",
            "zachking",
            "natgeo",
            "nike",
            "therock",
            "cristiano",
            "selenagomez",
            "kyliejenner",
            "leomessi"
        ]

        logger.info(f"👥 Сбор Reels из {len(profiles)} популярных профилей...")

        all_reels = []
        per_profile = max(3, limit // len(profiles))

        for profile in profiles:
            if len(all_reels) >= limit:
                break

            reels = self.collect_from_profile(profile, limit=per_profile)
            all_reels.extend(reels)
            logger.info(f"   @{profile}: +{len(reels)} Reels (всего: {len(all_reels)})")

        logger.info(f"\n📊 Итого: {len(all_reels)} Reels из профилей")
        return all_reels[:limit]

    def _extract_reel_data(self, item: Dict) -> Optional[Dict]:
        """Извлечь данные Reel из JSON ответа API"""
        try:
            # Проверяем что это видео
            is_video = item.get('is_video', False) or item.get('video_url')
            if not is_video:
                return None

            code = item.get('code', '')
            if not code:
                return None

            # Извлечение caption и хэштегов
            caption_data = item.get('caption', {})
            if isinstance(caption_data, dict):
                caption = caption_data.get('text', '')
            elif isinstance(caption_data, str):
                caption = caption_data
            else:
                caption = ''

            hashtags = []
            if caption:
                words = caption.split()
                hashtags = [
                    word.strip('#').strip().lower()
                    for word in words
                    if word.startswith('#') and len(word) > 1
                ]

            # Дата публикации
            taken_at = item.get('taken_at', 0)
            if taken_at:
                publish_date = datetime.fromtimestamp(taken_at, tz=timezone.utc)
            else:
                publish_date = datetime.now(timezone.utc)

            # Автор
            user = item.get('user', {})
            author = user.get('username', 'unknown')

            # Аудио
            music = item.get('music_metadata', {})
            audio_info = music.get('music_info', {}) if music else {}
            song_info = audio_info.get('music_asset_info', {}) if audio_info else {}
            audio_name = song_info.get('title', None)

            reel_data = {
                'reel_id': code,
                'url': f"https://www.instagram.com/reel/{code}/",
                'video_url': item.get('video_url', ''),
                'caption': caption[:2000] if caption else '',
                'hashtags': hashtags[:15],
                'audio_name': audio_name,
                'author': author,
                'publish_date': publish_date,
                'views': item.get('play_count', 0) or item.get('view_count', 0) or 0,
                'likes': item.get('like_count', 0) or 0,
                'comments': item.get('comment_count', 0) or 0,
                'shares': item.get('share_count', 0) or item.get('reshare_count', 0) or 0,
                'duration': item.get('video_duration', 0),
            }

            return reel_data

        except Exception as e:
            logger.error(f"❌ Ошибка извлечения данных: {e}")
            return None