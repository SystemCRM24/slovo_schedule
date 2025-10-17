from fastapi import APIRouter, Depends
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
    return await BitrixClient.get_all_specialist()


@router.get("/get_clients", status_code=200)
async def get_clients() -> list[BXClient]:
    """Получение списка клиентов из Bitrix CRM."""
    clients = await BitrixClient.get_all_clients()
    return [BXClient.model_validate(c) for c in clients]


@router.get("/get_schedules", status_code=200)
async def get_schedules(query: QueryDateRange = Depends()) -> list[BXAppointment]:
    """Получение расписания записей специалистов за указанный период."""
    appointments = await BitrixClient.get_all_appointments(query.start, query.end)
    bx_appintments = map(lambda a: BXAppointment.model_validate(a), appointments)
    response = list(filter(lambda a: a.is_valid(), bx_appintments))
    comments = await BitrixClient.get_comments_from_appointments_by_id(a.id for a in response)
    print('[DEBUG]', len(response), len(comments))
    for i, appointment in enumerate(response):
        appointment.parse_last_comment(comments[i])
    return response


@router.get("/get_work_schedules", status_code=200)
async def get_work_schedules(query: QueryDateRange = Depends()) -> list[BXSchedule]:
    schedules = await BitrixClient.get_all_schedules(query.start, query.end)
    bx_schedules = map(lambda s: BXSchedule.model_validate(s), schedules)
    filtered = filter(lambda s: s.is_valid(), bx_schedules)
    return list(filtered)


@router.get("/get_constants", status_code=200)
async def get_constants() -> dict:
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
