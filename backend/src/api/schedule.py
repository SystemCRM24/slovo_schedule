from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import HTTPException
from datetime import datetime, timedelta

from src.core import BXConstants, BitrixClient, Settings
from src.schemas.api import Schedule, BXSchedule
from src.logger import logger
from src.utils import BatchBuilder, Interval

from .service import create_schedule_massive as _create_schedule_massive



router = APIRouter(prefix="/schedule")


@router.post("/", status_code=201)
async def create_schedule(schedule: Schedule, bt: BackgroundTasks) -> Schedule :
    """Создание графика."""
    seti = BXConstants.schedule.entityTypeId
    fields = schedule.to_bx()
    data = await BitrixClient.create_crm_item(seti, fields)
    schedule.id = data['id']
    bt.add_task(logger.debug, f'Schedule id={schedule.id} was created.')
    return schedule


@router.post("/massive/", status_code=201)
async def create_schedule_massive(schedule: Schedule) -> list[BXSchedule]:
    """Создание графика на 1 год по шаблону schedule"""
    return await _create_schedule_massive(schedule)


@router.get("/{id}", status_code=200)
async def get_schedule(id: int, bt: BackgroundTasks) -> BXSchedule:
    seti = BXConstants.schedule.entityTypeId
    data = await BitrixClient.get_crm_item(seti, id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Schedule id={id} not found")
    schedule = BXSchedule(**data)
    bt.add_task(logger.debug, f'Schedule id={id} was received.')
    return schedule


@router.put("/{id}", status_code=200)
async def update_schedule(id: int, schedule: Schedule, bt: BackgroundTasks) -> Schedule:
    seti = BXConstants.schedule.entityTypeId
    fields = schedule.to_bx()
    updated_data = await BitrixClient.update_crm_item(seti, id, fields)
    bt.add_task(logger.debug, f"Appointment id={id} was updated.")
    return schedule


@router.put('/massive/{id}', status_code=200)
async def update_schedule_massive(id: int, schedule: Schedule, bt: BackgroundTasks):
    """Массовое обновление графиков."""
    start = datetime.fromisoformat(schedule.date).replace(tzinfo=Settings.TIMEZONE)
    end = start + timedelta(days=365)
    schedules = await BitrixClient.get_specialists_schedules(
        start.isoformat(),
        end.isoformat(),
        (schedule.specialist, )
    )
    template = list(map(lambda i: Interval.from_js_timestamp(*(i.split(':'))), schedule.intervals))
    builder = BatchBuilder('crm.item.update')
    batches = {}
    for s in schedules:
        schedule_date = s.get(BXConstants.schedule.uf.date, None)
        if not schedule_date:
            continue
        schedule_date = datetime.fromisoformat(schedule_date).replace(tzinfo=Settings.TIMEZONE)
        if schedule_date.weekday() != start.weekday():
            continue
        schedule_intervals = []
        for i in template:
            interval_start = i.start.replace(
                year=schedule_date.year, 
                month=schedule_date.month,
                day=schedule_date.day
            )
            interval_end = i.end.replace(
                year=schedule_date.year, 
                month=schedule_date.month,
                day=schedule_date.day
            )
            interval_start = int(interval_start.timestamp()) * 1000
            interval_end = int(interval_end.timestamp()) * 1000
            schedule_intervals.append(f'{interval_start}:{interval_end}')
        fields = {BXConstants.schedule.uf.intervals: schedule_intervals}
        builder.params = {
            "entityTypeId": BXConstants.schedule.entityTypeId, 
            "id": s.get('id'), 
            "fields": fields
        }
        batches[s.get('id')] = builder.build()
    result = await BitrixClient.call_batch(batches)
    default = {}
    if isinstance(result, list):
        return result
    return [BXSchedule.model_validate(i.get('item', default)) for i in result.values()]


@router.delete("/{id}", status_code=204)
async def delete_schedule(id: int, bt: BackgroundTasks):
    seti = BXConstants.schedule.entityTypeId
    result = await BitrixClient.delete_crm_item(seti, id)
    if not result:
        raise HTTPException(404, f'Schedule id={id} not found.')
    bt.add_task(logger.debug, f'Schedule id={id} was deleted.')


# @router.delete('/massive/{id}', status_code=204)
# async def delete_schedule_massive(id: int, bt: BackgroundTasks):
#     seti = BXConstants.schedule.entityTypeId
#     schedule_data = await BitrixClient.get_crm_item(seti, id)
#     date = schedule_data.get(BXConstants.schedule.uf.date, None)
#     specialist = schedule_data.get(BXConstants.schedule.uf.specialist, None)
#     if date is None or specialist is None:
#         return
#     start = datetime.fromisoformat(date).replace(tzinfo=Settings.TIMEZONE)
#     end = start + timedelta(days=365)
#     schedules = await BitrixClient.get_specialists_schedules(
#         start.isoformat(),
#         end.isoformat(),
#         (specialist, )
#     )