from fastapi import APIRouter
import asyncio

from .handler import Handler


router = APIRouter(prefix="", tags=['AppointPlan'])


@router.post("/repetative", status_code=200)
async def repetative(data: str):
    """Боевой метод - проставляет "бесконечные" занятия"""
    handler = Handler(data)
    asyncio.create_task(handler.run())


@router.post('/test_repetative', status_code=200)
async def repetative_test(data: str):
    """Метод для отладки"""
    handler = Handler(data)
    return await handler.run()
