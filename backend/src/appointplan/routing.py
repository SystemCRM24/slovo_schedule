import asyncio
from fastapi import APIRouter

from .handler import Handler


router = APIRouter(prefix="", tags=['AppointPlan'])


@router.post("/handle", status_code=200)
async def handle(data: str):
    """Боевой метод. Соединение не удерживает."""
    handler = Handler(data)
    asyncio.create_task(handler.run())


@router.post("/test_handle", status_code=200)
async def test_handle(data: str):
    """Метод для тестирования. Ожидает и возвращает результат работы."""
    handler = Handler(data)
    return await handler.run()
