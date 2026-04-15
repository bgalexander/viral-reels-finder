"""
🚀 Автоматический сбор популярных Reels
Запуск: python scripts/auto_collect.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.collectors.auto_collector import AutoReelsCollector
from app.database.connection import SessionLocal
from app.services.reels_service import ReelsService


def auto_collect():
    """Автоматический сбор и сохранение Reels"""

    print("=" * 60)
    print("🚀 АВТОМАТИЧЕСКИЙ СБОР ПОПУЛЯРНЫХ REELS")
    print("=" * 60)

    # Инициализация
    try:
        collector = AutoReelsCollector()
    except ValueError as e:
        print(f"\n{e}")
        return

    db = SessionLocal()
    service = ReelsService(db)

    try:
        # ==========================================
        # Способ 1: Сбор по хэштегам
        # ==========================================
        print("\n📌 ЭТАП 1: Сбор по популярным хэштегам")
        print("-" * 40)

        trending_hashtags = [
            "viral", "trending", "reels",
            "funny", "comedy", "memes",
            "travel", "food", "fitness",
            "fashion", "beauty", "music"
        ]

        hashtag_reels = collector.collect_trending(
            hashtags=trending_hashtags,
            limit=30
        )

        # ==========================================
        # Способ 2: Сбор из популярных профилей
        # ==========================================
        print("\n📌 ЭТАП 2: Сбор из популярных профилей")
        print("-" * 40)

        profile_reels = collector.collect_from_top_profiles(limit=20)

        # ==========================================
        # Объединяем и сохраняем
        # ==========================================
        all_reels = hashtag_reels + profile_reels

        # Убираем дубликаты
        seen = set()
        unique_reels = []
        for reel in all_reels:
            if reel['reel_id'] not in seen:
                seen.add(reel['reel_id'])
                unique_reels.append(reel)

        print(f"\n📊 Собрано {len(unique_reels)} уникальных Reels")
        print("=" * 60)

        # Сохраняем в БД
        print("\n💾 Сохранение в базу данных...")

        saved = 0
        updated = 0

        for i, reel_data in enumerate(unique_reels, 1):
            try:
                reel = service.create_or_update_reel(reel_data)
                is_new = reel.created_at == reel.updated_at

                status = "NEW" if is_new else "UPD"
                viral = "🔥" if reel.is_viral else "  "

                print(
                    f"  [{i}/{len(unique_reels)}] {status} {viral} "
                    f"{reel.reel_id[:15]:<15} "
                    f"Views: {reel_data.get('views', 0):>10,} | "
                    f"Likes: {reel_data.get('likes', 0):>8,} | "
                    f"Score: {reel.viral_score:>10,.0f}"
                )

                if is_new:
                    saved += 1
                else:
                    updated += 1

            except Exception as e:
                print(f"  [{i}] ❌ Ошибка: {e}")

        db.commit()

        # Итоги
        print("\n" + "=" * 60)
        print("📊 ИТОГИ СБОРА:")
        print(f"   ✅ Новых Reels: {saved}")
        print(f"   🔄 Обновлено: {updated}")
        print(f"   📁 Всего в БД: {service.get_total_count()}")

        # Топ 5 по viral score
        print("\n🏆 ТОП-5 ВИРУСНЫХ REELS:")
        top_reels = service.get_viral_reels(limit=5)
        for i, reel in enumerate(top_reels, 1):
            print(
                f"   {i}. {reel.reel_id[:20]} | "
                f"Score: {reel.viral_score:,.0f} | "
                f"Views: {reel.views:,}"
            )

        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⏹️ Остановлено пользователем")
        db.commit()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    auto_collect()