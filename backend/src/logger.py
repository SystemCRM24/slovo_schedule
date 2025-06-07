from loguru import logger
import sys
from fastapi import BackgroundTasks

from .core import Settings

# Удален стандартный обработчик
logger.remove()

debug_template = (
    "<level>{level:<7}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{message}"
)

# Основной логгер
logger.add(
    sys.stdout,
    level='DEBUG' if Settings.MODE == 'dev' else 'INFO',
    format=debug_template,
    filter=lambda r: r['level'].no < logger.level('CRITICAL').no,
    enqueue=True
)

critical_template = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level}</level> | "
    "{message}"
)

logger.add(
    sys.stdout,
    level='CRITICAL',
    format=critical_template,
    enqueue=True
)

# На ошибки приложения
logger.add(
    "error.log",
    level='CRITICAL',
    format=critical_template,
    rotation='10 MB',
    enqueue=True
    # backtrace=True,
)
