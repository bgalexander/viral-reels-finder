"""
Главный файл FastAPI приложения
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router
from app.database.connection import init_db
from app.services.scheduler_service import SchedulerService
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальный планировщик
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    global scheduler

    # Startup
    logger.info("🚀 Запуск приложения...")

    # Инициализация БД
    init_db()

    # Запуск планировщика
    scheduler = SchedulerService()
    scheduler.start()

    logger.info("✅ Приложение запущено")

    yield

    # Shutdown
    logger.info("🛑 Остановка приложения...")
    if scheduler:
        scheduler.stop()
    logger.info("✅ Приложение остановлено")


# Создание приложения
app = FastAPI(
    title="Viral Reels Finder API",
    description="API для поиска и анализа вирусных Instagram Reels",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.scheduler.running if scheduler else False
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )