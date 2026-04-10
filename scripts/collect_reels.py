"""
Скрипт для ручного запуска сбора Reels
"""
import sys
from pathlib import Path
import argparse

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from app.database.connection import get_db_context
from app.services.reels_service import ReelsService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_from_all_sources():
    """Собрать Reels из всех активных источников"""
    logger.info("🚀 Запуск сбора из всех источников...")

    with get_db_context() as db:
        service = ReelsService(db)
        service.collect_reels_from_sources()

    logger.info("✅ Сбор завершен!")


def collect_from_hashtag(hashtag: str, limit: int = 50):
    """Собрать Reels из конкретного хэштега"""
    logger.info(f"🚀 Сбор Reels из хэштега #{hashtag}...")

    with get_db_context() as db:
        service = ReelsService(db)

        # Добавляем источник, если его нет
        service.add_source("hashtag", hashtag)

        # Собираем данные
        reels_data = service.collector.collect_from_hashtag(hashtag, limit=limit)

        # Сохраняем в БД
        for reel_data in reels_data:
            service.create_or_update_reel(reel_data)

        logger.info(f"✅ Собрано и сохранено {len(reels_data)} Reels")


def collect_from_account(username: str, limit: int = 50):
    """Собрать Reels из конкретного аккаунта"""
    logger.info(f"🚀 Сбор Reels из аккаунта @{username}...")

    with get_db_context() as db:
        service = ReelsService(db)

        # Добавляем источник, если его нет
        service.add_source("account", username)

        # Собираем данные
        reels_data = service.collector.collect_from_account(username, limit=limit)

        # Сохраняем в БД
        for reel_data in reels_data:
            service.create_or_update_reel(reel_data)

        logger.info(f"✅ Собрано и сохранено {len(reels_data)} Reels")


def update_metrics():
    """Обновить метрики для существующих Reels"""
    logger.info("🔄 Обновление метрик...")

    with get_db_context() as db:
        service = ReelsService(db)
        service.update_metrics()

    logger.info("✅ Метрики обновлены!")


def recalculate_scores():
    """Пересчитать оценки вирусности"""
    logger.info("🔄 Пересчет оценок вирусности...")

    with get_db_context() as db:
        service = ReelsService(db)
        service.recalculate_scores()

    logger.info("✅ Оценки пересчитаны!")


def main():
    """Главная функция с парсером аргументов"""
    parser = argparse.ArgumentParser(description="Сбор Instagram Reels")

    subparsers = parser.add_subparsers(dest='command', help='Команды')

    # Команда: collect-all
    subparsers.add_parser('collect-all', help='Собрать из всех активных источников')

    # Команда: collect-hashtag
    hashtag_parser = subparsers.add_parser('collect-hashtag', help='Собрать из хэштега')
    hashtag_parser.add_argument('hashtag', help='Название хэштега (без #)')
    hashtag_parser.add_argument('--limit', type=int, default=50, help='Максимум постов')

    # Команда: collect-account
    account_parser = subparsers.add_parser('collect-account', help='Собрать из аккаунта')
    account_parser.add_argument('username', help='Username аккаунта')
    account_parser.add_argument('--limit', type=int, default=50, help='Максимум постов')

    # Команда: update-metrics
    subparsers.add_parser('update-metrics', help='Обновить метрики')

    # Команда: recalculate
    subparsers.add_parser('recalculate', help='Пересчитать оценки вирусности')

    args = parser.parse_args()

    if args.command == 'collect-all':
        collect_from_all_sources()

    elif args.command == 'collect-hashtag':
        collect_from_hashtag(args.hashtag, args.limit)

    elif args.command == 'collect-account':
        collect_from_account(args.username, args.limit)

    elif args.command == 'update-metrics':
        update_metrics()

    elif args.command == 'recalculate':
        recalculate_scores()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()