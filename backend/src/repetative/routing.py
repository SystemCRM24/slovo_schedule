from fastapi import APIRouter

from .handler import Handler


router = APIRouter(prefix="", tags=['AppointPlan'])


@router.post("/repetative", status_code=200)
async def repetative(data: str):
    """Боевой метод - проставляет "бесконечные" занятия"""


@router.post('/test_repetative', status_code=200)
async def repetative_test(data: str):
    """Метод для отладки"""
    handler = Handler(data)
    return await handler.run()
