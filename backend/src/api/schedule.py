from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import HTTPException

from src.core import BXConstants, BitrixClient
from src.schemas.api import Schedule, BXSchedule
from src.logger import logger


router = APIRouter(prefix="/schedule")


@router.post("/", status_code=201)
async def create_schedule(schedule: Schedule, bt: BackgroundTasks) -> Schedule:
    seti = BXConstants.schedule.entityTypeId
    fields = schedule.to_bx()
    data = await BitrixClient.create_crm_item(seti, fields)
    schedule.id = data['id']
    bt.add_task(logger.debug, f'Schedule id={schedule.id} was created.')
    return schedule


@router.get("/{id}", status_code=200)
async def get_schedule(id: int, bt: BackgroundTasks) -> BXSchedule:
    seti = BXConstants.schedule.entityTypeId
    data = await BitrixClient.get_crm_item(seti, id)
    if data is None:
        raise HTTPException(status_code=404, detail="Schedule id={id} not found")
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


@router.delete("/{id}", status_code=204)
async def delete_schedule(id: int, bt: BackgroundTasks):
    seti = BXConstants.schedule.entityTypeId
    result = await BitrixClient.delete_crm_item(seti, id)
    if not result:
        raise HTTPException(404, f'Schedule id={id} not found.')
    bt.add_task(logger.debug, f'Schedule id={id} was deleted.')
