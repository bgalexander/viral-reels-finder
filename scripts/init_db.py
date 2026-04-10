"""
Скрипт инициализации базы данных
"""
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from app.database.connection import init_db, get_db_context
from app.models.models import Source
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_initial_sources():
    """Создать начальные источники для тестирования"""

    initial_sources = [
        {"source_type": "hashtag", "name": "travel"},
        {"source_type": "hashtag", "name": "fitness"},
        {"source_type": "hashtag", "name": "food"},
        {"source_type": "hashtag", "name": "fashion"},
        {"source_type": "hashtag", "name": "comedy"},
        {"source_type": "hashtag", "name": "music"},
        {"source_type": "hashtag", "name": "dance"},
        {"source_type": "hashtag", "name": "art"},
    ]

    with get_db_context() as db:
        for source_data in initial_sources:
            # Проверяем, существует ли уже
            existing = db.query(Source).filter(
                Source.name == source_data["name"]
            ).first()

            if not existing:
                source = Source(**source_data)
                db.add(source)
                logger.info(f"✅ Добавлен источник: {source_data['source_type']}:{source_data['name']}")
            else:
                logger.info(f"⏭️  Источник уже существует: {source_data['name']}")

        db.commit()


def main():
    """Главная функция"""
    logger.info("🚀 Инициализация базы данных...")

    # Создаем таблицы
    init_db()

    # Создаем начальные источники
    logger.info("📝 Создание начальных источников...")
    create_initial_sources()

    logger.info("✅ Инициализация завершена!")


if __name__ == "__main__":
    main()