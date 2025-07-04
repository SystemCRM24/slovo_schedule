from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import HTTPException

from src.core import BitrixClient, BXConstants
from src.schemas.api import Appointment, BXAppointment
from src.logger import logger


router = APIRouter(prefix="/appointment")


@router.post("/", status_code=201)
async def create_appointment(appointment: Appointment, bt: BackgroundTasks) -> Appointment:
    """Создание элемента смарт-процесса - расписание"""
    aety = BXConstants.appointment.entityTypeId
    fields = appointment.to_bx()
    data = await BitrixClient.create_crm_item(aety, fields)
    appointment.id = data['id']
    bt.add_task(logger.debug, f'Appointment id={appointment.id} was created.')
    return appointment


@router.get("/{id}", status_code=200)
async def get_appointment(id: int, bt: BackgroundTasks) -> BXAppointment:
    """Получение элемента смарт-процесса Расписание"""
    aety = BXConstants.appointment.entityTypeId
    data = await BitrixClient.get_crm_item(aety, id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Appointment id={id} not found.")
    appointment = BXAppointment(**data)
    bt.add_task(logger.debug, f'Appointment id={id} was received.')
    return appointment


@router.put("/{id}", status_code=200)
async def update_appointment(id: int, appointment: Appointment, bt: BackgroundTasks) -> Appointment:
    """Обновление элемента смарт-процесса расписание"""
    aety = BXConstants.appointment.entityTypeId
    fields = appointment.to_bx()
    updated_data = await BitrixClient.update_crm_item(aety, id, fields)
    bt.add_task(logger.debug, f"Appointment id={id} was updated.")
    bt.add_task(BitrixClient.init_bizporc, id)
    return appointment


@router.delete("/{id}", status_code=204)
async def delete_appointment(id: int, bt: BackgroundTasks):
    """Удаляет элемент смарт процесса расписание."""
    aety = BXConstants.appointment.entityTypeId
    result = await BitrixClient.delete_crm_item(aety, id)
    if not result:
        raise HTTPException(404, f'Appointment id={id} not found.')
    bt.add_task(logger.debug, f'Appointment id={id} was deleted.')
