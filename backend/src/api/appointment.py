from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import HTTPException
from datetime import datetime, timedelta
import asyncio

from src.core import BitrixClient, BXConstants, Settings
from src.schemas.api import Appointment, BXAppointment
from src.logger import logger
from src.utils import BatchBuilder


router = APIRouter(prefix="/appointment")


@router.post("/", status_code=201)
async def create_appointment(appointment: Appointment, bt: BackgroundTasks) -> BXAppointment:
    """Создание элемента смарт-процесса - расписание"""
    aety = BXConstants.appointment.entityTypeId
    fields = appointment.to_bx()
    data = await BitrixClient.create_crm_item(aety, fields)
    appointment = BXAppointment.model_validate(data)
    bt.add_task(logger.debug, f'Appointment id={appointment.id} was created.')
    return appointment


@router.get("/{id}", status_code=200)
async def get_appointment(id: int, bt: BackgroundTasks) -> BXAppointment:
    """Получение элемента смарт-процесса Расписание"""
    aety = BXConstants.appointment.entityTypeId
    data, comments = await asyncio.gather(
        BitrixClient.get_crm_item(aety, id),
        BitrixClient.get_comments_list(id)
    )
    if data is None:
        raise HTTPException(status_code=404, detail=f"Appointment id={id} not found.")
    appointment = BXAppointment.model_validate(data)
    appointment.parse_last_comment(comments)
    bt.add_task(logger.debug, f'Appointment id={id} was received.')
    return appointment


@router.put("/{id}", status_code=200)
async def update_appointment(id: int, appointment: Appointment, bt: BackgroundTasks) -> BXAppointment:
    """Обновление элемента смарт-процесса расписание"""
    await BitrixClient.init_bizporc(id)
    aety = BXConstants.appointment.entityTypeId
    fields = appointment.to_bx()
    data, comment = await asyncio.gather(
        BitrixClient.update_crm_item(aety, id, fields),
        BitrixClient.get_comments_list(id)
    )
    appointment: BXAppointment = BXAppointment.model_validate(data)
    appointment.parse_last_comment(comment)
    bt.add_task(logger.debug, f"Appointment id={id} was updated.")
    return appointment


@router.put('/massive/{id}', status_code=200)
async def update_appointment_massive(id: int, template: Appointment):
    """Массовый перенос занятий по шаблону"""

    def get_date(raw_appointment):
        return (
            datetime.fromisoformat(raw_appointment.get('ufCrm3StartDate')).replace(tzinfo=Settings.TIMEZONE),
            datetime.fromisoformat(raw_appointment.get('ufCrm3EndDate')).replace(tzinfo=Settings.TIMEZONE)
        )
    
    new_start = datetime.fromisoformat(template.start)
    new_end = datetime.fromisoformat(template.end)

    aety = BXConstants.appointment.entityTypeId
    data = await BitrixClient.get_crm_item(aety, id)
    tstart, tend = get_date(data)
    all_appointments = await BitrixClient.get_specialists_appointments(
        tstart.replace(hour=0, minute=0, second=0).isoformat(),
        (tstart + timedelta(days=365)).isoformat(),
        (data.get('assignedById'), )
    )
    tpatient = data.get('ufCrm3Children')
    tstatus = data.get('ufCrm3Status')
    tcode = data.get('ufCrm3Code')
    tdeal = data.get('ufCrm3Dealid')
    tweekday = tstart.weekday()
    tstart_time, tend_time = tstart.time(), tend.time()
    start_delta, end_delta = new_start - tstart, new_end - tend
    to_update = {}
    builder = BatchBuilder('crm.item.update')
    for raw_app in all_appointments:
        # СУПЕР ГОВНОКОД ФИЛЬТРАЦИИ
        if tpatient != raw_app.get('ufCrm3Children'):
            continue
        if tstatus != raw_app.get('ufCrm3Status'):
            continue
        if tcode != raw_app.get('ufCrm3Code'):
            continue
        if tdeal != raw_app.get('ufCrm3Dealid'):
            continue
        start, end = get_date(raw_app)
        if tweekday != start.weekday():
            continue
        if tstart_time != start.time():
            continue
        if tend_time != end.time():
            continue
        # И наконец, мы получаем нужные занятия
        fields = {
            BXConstants.appointment.uf.specialist: template.specialist,
            BXConstants.appointment.uf.patient: template.patient,
            BXConstants.appointment.uf.start: (start + start_delta).isoformat(),
            BXConstants.appointment.uf.end: (end + end_delta).isoformat()
        }
        raw_app_id = raw_app.get('id')
        builder.params = {"entityTypeId": aety, 'id': raw_app_id, 'fields': fields}
        to_update[raw_app_id] = builder.build()
    await BitrixClient.init_bizporc(*to_update)
    return await BitrixClient.call_batch(to_update)


@router.put("/rollback/{id}", status_code=200)
async def rollback_appointment(id: int, bt: BackgroundTasks) -> BXAppointment:
    """Откатывает изменения занятия на 1 шаг назад"""
    aety = BXConstants.appointment.entityTypeId
    data, comments = await asyncio.gather(
        BitrixClient.get_crm_item(aety, id),
        BitrixClient.get_comments_list(id)
    )
    appointment = BXAppointment.model_validate(data)
    appointment.parse_last_comment(comments)
    if len(comments) > 0:
        previous = Appointment(
            specialist=appointment.old_specialist,
            patient=appointment.old_patient,
            start=appointment.old_start,
            end=appointment.old_end,
            code=appointment.old_code,
            status=appointment.old_status
        )
        fields = previous.to_bx()
        updated_data = await BitrixClient.update_crm_item(aety, id, fields)
        appointment = BXAppointment.model_validate(updated_data)
        comment = comments.pop(0)
        await BitrixClient.delete_comment(comment)
        appointment.parse_last_comment(comments)
    return appointment


@router.delete("/{id}", status_code=204)
async def delete_appointment(id: int, bt: BackgroundTasks):
    """Удаляет элемент смарт процесса расписание."""
    aety = BXConstants.appointment.entityTypeId
    result = await BitrixClient.delete_crm_item(aety, id)
    if not result:
        raise HTTPException(404, f'Appointment id={id} not found.')
    bt.add_task(logger.debug, f'Appointment id={id} was deleted.')


@router.delete('/massive/{id}', status_code=200)
async def delete_appointment_massive(id: int, bt: BackgroundTasks) -> list[BXAppointment]:
    template = await get_appointment(id, bt)
    template_start = datetime.fromisoformat(template.start)                  # type:ignore
    appointments = await BitrixClient.get_specialists_appointments(
        template_start.replace(hour=0, minute=0, second=0).isoformat(),
        (template_start + timedelta(days=380)).isoformat(),
        (template.specialist, )
    )
    response = []
    batches = {}
    builder = BatchBuilder("crm.item.delete")
    for raw in appointments:
        appointment = BXAppointment.model_validate(raw)
        is_patient = template.patient == appointment.patient
        is_code = template.code == appointment.code
        app_start = datetime.fromisoformat(appointment.start)       # type: ignore
        is_weekday = template_start.weekday() == app_start.weekday()
        if not (is_patient and is_code and is_weekday):
            continue
        app_start = app_start.replace(
            year=template_start.year,
            month=template_start.month,
            day=template_start.day
        )
        if template_start != app_start:
            continue
        builder.params = {
            "entityTypeId": BXConstants.appointment.entityTypeId, 
            "id": appointment.id
        }
        batches[appointment.id] = builder.build()
        response.append(appointment)
    await BitrixClient.call_batch(batches)
    return response
