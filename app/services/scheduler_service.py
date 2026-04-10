"""
Сервис планировщика задач
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.database.connection import get_db_context
from app.services.reels_service import ReelsService
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulerService:
    """Сервис для управления запланированными задачами"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(
            daemon=True,
            timezone='UTC'
        )
        self._setup_jobs()

    def _setup_jobs(self):
        """Настройка запланированных задач"""

        # Сбор новых Reels каждые 30 минут
        self.scheduler.add_job(
            func=self._collect_reels_job,
            trigger=IntervalTrigger(minutes=settings.COLLECT_INTERVAL_MINUTES),
            id='collect_reels',
            name='Collect new Reels',
            replace_existing=True,
            max_instances=1
        )
        logger.info(f"📅 Задача сбора Reels: каждые {settings.COLLECT_INTERVAL_MINUTES} минут")

        # Обновление метрик каждые 2 часа
        self.scheduler.add_job(
            func=self._update_metrics_job,
            trigger=IntervalTrigger(hours=settings.UPDATE_METRICS_INTERVAL_HOURS),
            id='update_metrics',
            name='Update engagement metrics',
            replace_existing=True,
            max_instances=1
        )
        logger.info(f"📅 Задача обновления метрик: каждые {settings.UPDATE_METRICS_INTERVAL_HOURS} часа")

        # Пересчет оценок вирусности раз в день в 3:00 UTC
        self.scheduler.add_job(
            func=self._recalculate_scores_job,
            trigger=CronTrigger(hour=3, minute=0),
            id='recalculate_scores',
            name='Recalculate viral scores',
            replace_existing=True,
            max_instances=1
        )
        logger.info("📅 Задача пересчета оценок: ежедневно в 3:00 UTC")

    def _collect_reels_job(self):
        """Задача сбора новых Reels"""
        logger.info("🚀 Запуск задачи сбора Reels")
        try:
            with get_db_context() as db:
                service = ReelsService(db)
                service.collect_reels_from_sources()
            logger.info("✅ Задача сбора Reels завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче сбора Reels: {e}")

    def _update_metrics_job(self):
        """Задача обновления метрик"""
        logger.info("🚀 Запуск задачи обновления метрик")
        try:
            with get_db_context() as db:
                service = ReelsService(db)
                service.update_metrics()
            logger.info("✅ Задача обновления метрик завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче обновления метрик: {e}")

    def _recalculate_scores_job(self):
        """Задача пересчета оценок вирусности"""
        logger.info("🚀 Запуск задачи пересчета оценок")
        try:
            with get_db_context() as db:
                service = ReelsService(db)
                service.recalculate_scores()
            logger.info("✅ Задача пересчета оценок завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка в задаче пересчета оценок: {e}")

    def start(self):
        """Запустить планировщик"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Планировщик запущен")

    def stop(self):
        """Остановить планировщик"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Планировщик остановлен")

    def get_jobs(self):
        """Получить список всех задач"""
        return self.scheduler.get_jobs()