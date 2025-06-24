import asyncio
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from src.logger import logger


async def handle_http_exception(request, exc: HTTPException) -> JSONResponse:
    """Обрабатывает и логгирует http исключения"""
    async def coro():
        await asyncio.sleep(0.02)    # trololo
        logger.error(exc.detail)
    asyncio.create_task(coro())
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})


def extract(obj) -> dict:
    """Используется для извлечения данных из объекта в словарь"""
    result = {}
    if isinstance(obj, type):
        attrs = dir(obj)
    elif isinstance(obj, dict):
        return obj
    else:
        return obj
    for key in attrs:
        if key.startswith('__'):
            continue
        value = getattr(obj, key)
        if isinstance(value, type):
            result[key] = extract(value)
        else:
            result[key] = value
    return result
