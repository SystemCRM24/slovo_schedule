from loguru import logger
import sys
from fastapi import BackgroundTasks

from .core import Settings

# Удален стандартный обработчик
logger.remove()

debug_template = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{message}"
)

# Основной логгер
logger.add(
    sys.stdout,
    level='DEBUG' if Settings.MODE == 'dev' else 'INFO',
    format=debug_template,
    filter=lambda r: r['level'].no < logger.level('ERROR').no
)

# HTTPException, которые сами рейзим
error_template = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | {message}"
logger.add(
    sys.stdout,
    level='ERROR',
    format=error_template
)

# На ошибки приложения
logger.add(
    "error.log",
    level='CRITICAL',
    format=error_template,
    rotation='10 MB',
    enqueue=True
    # backtrace=True,
)
