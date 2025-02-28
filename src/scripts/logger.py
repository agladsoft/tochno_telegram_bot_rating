import os
import sys

from loguru import logger

# Определяем базовый каталог и общую директорию для логов
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logging")
os.makedirs(LOG_DIR, exist_ok=True)

# Путь к файлу логов
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Очищаем стандартные настройки логирования Loguru
logger.remove()

# Добавляем файловый sink для записи логов в один файл
logger.add(
    LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="10 MB",  # Ротация файла при достижении 10 МБ
    compression="zip",  # Сжатие старых логов в архивы
    level="DEBUG",  # Фиксируем логи уровня DEBUG и выше
    enqueue=True,  # Асинхронная запись логов
)
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG"
)


def get_logger():
    """
    Возвращает настроенный логгер Loguru для использования в приложении.

    Используйте данную функцию в любом модуле:

        from custom_logger import get_logger
        logger = get_logger()
        logger.info("Сообщение лога")
    """
    return logger


# Инициализация логгера для текущего модуля
app_logger = get_logger()

