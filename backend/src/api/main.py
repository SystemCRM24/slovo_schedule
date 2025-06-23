from fastapi import APIRouter, Depends
from typing import Dict
from src.utils import extract

from src.core import BitrixClient, BXConstants
from src.schemas.api import (
    BXSpecialist, 
    BXClient, 
    QueryDateRange,
    BXAppointment,
    BXSchedule
)


router = APIRouter(prefix="")


@router.get("/get_specialist", status_code=200)
async def get_specialists() -> list[BXSpecialist]:
    """Получение списка специалистов из Bitrix."""
    specialists = await BitrixClient.get_all_specialist()
    return [BXSpecialist(**s) for s in specialists]


@router.get("/get_clients", status_code=200)
async def get_clients() -> list[BXClient]:
    """Получение списка клиентов из Bitrix CRM."""
    clients = await BitrixClient.get_all_clients()
    return [BXClient(**c) for c in clients]


@router.get("/get_schedules", status_code=200)
async def get_schedules(query: QueryDateRange = Depends()) -> list[BXAppointment]:
    """Получение расписания записей специалистов за указанный период."""
    appointments = await BitrixClient.get_all_appointments(query.start, query.end)
    bx_appintments = map(lambda a: BXAppointment(**a), appointments)
    filtered = filter(lambda a: a.is_valid(), bx_appintments)
    return list(filtered)


@router.get("/get_work_schedules", status_code=200)
async def get_work_schedules(query: QueryDateRange = Depends()) -> list[BXSchedule]:
    schedules = await BitrixClient.get_all_schedules(query.start, query.end)
    bx_schedules = map(lambda s: BXSchedule(**s), schedules)
    filtered = filter(lambda s: s.is_valid(), bx_schedules)
    return list(filtered)


@router.get("/get_constants", status_code=200)
async def get_constants() -> Dict:
    """Возвращает содержимое BXConstants в виде словаря."""
    bx_dict = {}

    for key in dir(BXConstants):
        if key.startswith('__'):
            continue
        value = getattr(BXConstants, key)

        if isinstance(value, type):
            bx_dict[key] = extract(value)
        elif isinstance(value, dict):
            bx_dict[key] = value

    return bx_dict