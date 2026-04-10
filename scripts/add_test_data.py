"""Добавление тестовых данных для демонстрации"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database.connection import get_db_context
from app.services.reels_service import ReelsService
from datetime import datetime, timezone, timedelta
import random


def create_test_reels():
    """Создать тестовые Reels"""
    print("🚀 Создание тестовых данных...\n")

    test_reels = []
    hashtags_options = [
        ['travel', 'vacation', 'adventure', 'explore'],
        ['fitness', 'workout', 'gym', 'health'],
        ['food', 'cooking', 'recipe', 'foodie'],
        ['fashion', 'style', 'ootd', 'outfit'],
        ['nature', 'landscape', 'photography', 'beautiful'],
        ['dance', 'music', 'entertainment', 'fun'],
        ['art', 'creative', 'design', 'artist'],
        ['pets', 'dogs', 'cats', 'animals']
    ]

    audio_options = [
        'Trending Song 2024',
        'Viral Audio Mix',
        'Popular Beat',
        'Chill Vibes',
        'Upbeat Track',
        'Emotional Music',
        'Dance Hit',
        'Catchy Tune'
    ]

    for i in range(1, 51):  # 50 тестовых Reels
        hashtags = random.choice(hashtags_options)

        # Генерируем реалистичные метрики
        views = random.randint(5000, 500000)
        likes = int(views * random.uniform(0.03, 0.15))
        comments = int(views * random.uniform(0.005, 0.03))

        test_reels.append({
            'reel_id': f'test_{i:03d}_{random.randint(1000, 9999)}',
            'url': f'https://instagram.com/reel/test_{i:03d}/',
            'video_url': f'https://example.com/video_{i}.mp4',
            'caption': f'Amazing content #{i}! 🔥 ' + ' '.join([f'#{tag}' for tag in hashtags[:3]]),
            'hashtags': hashtags,
            'audio_name': random.choice(audio_options),
            'publish_date': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72)),
            'views': views,
            'likes': likes,
            'comments': comments,
            'duration': random.uniform(15, 60)
        })

    with get_db_context() as db:
        service = ReelsService(db)

        for idx, reel_data in enumerate(test_reels, 1):
            reel = service.create_or_update_reel(reel_data)

            # Показываем прогресс
            viral_mark = "🔥" if reel.is_viral else "  "
            print(
                f"{viral_mark} [{idx:2d}/50] {reel.reel_id} - Views: {reel.views:>7,} | Likes: {reel.likes:>6,} | Viral Score: {reel.viral_score:>10,.0f}")

    print(f"\n✅ Создано {len(test_reels)} тестовых Reels!")
    print("\n" + "=" * 70)
    print("🎉 ГОТОВО! Теперь:")
    print("   1. Обновите страницу дашборда: http://localhost:8501")
    print("   2. Или откройте API: http://localhost:8000/docs")
    print("=" * 70)


if __name__ == "__main__":
    create_test_reels()