from typing import List
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from .models.base_models import (
    DateRange,
    SpecialistResponse,
    ClientResponse,
    Patient,
    Appointment,
    ScheduleResponse,
    WorkInterval,
    WorkSchedule,
    WorkScheduleResponse
)
from .appointment import router as appointment_router
from .schedule import router as schedule_router
from app.bitrix import BITRIX
from app.settings import Settings
import logging
from .constants import constants


logging.basicConfig(level=logging.INFO)


router = APIRouter(prefix='/front', tags=['front'])

router.include_router(appointment_router)
router.include_router(schedule_router)


@router.get('/get_specialist', status_code=200, response_model=List[SpecialistResponse])
async def get_specialist():
    """Получение списка специалистов из Bitrix."""
    try:
        response = await BITRIX.call(
            'user.get',
            {'@UF_DEPARTMENT': list(constants.departments.keys())},
            raw=True
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        specialists = [
            SpecialistResponse(
                id=int(user['ID']),
                name=f"{user['LAST_NAME']} {user['NAME'][0]}.",
                departments=[constants.departments.get(str(d)) for d in user.get('UF_DEPARTMENT', [])]
            )
            for user in response['result']
        ]
        return specialists
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка специалистов из Bitrix: {str(e)}")


@router.get('/get_clients', status_code=200, response_model=List[ClientResponse])
async def get_clients():
    """Получение списка клиентов из Bitrix CRM."""
    try:
        params = {
            'filter': {'TYPE_ID': "CLIENT"},
            'select': ['ID', 'NAME', 'LAST_NAME']
        }
        clients = await BITRIX.get_all('crm.contact.list', params)
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{clients}")
        return [
            ClientResponse(
                id=int(client['ID']),
                full_name=f"{client['NAME']} {client['LAST_NAME']}" if client['LAST_NAME'] else client['NAME']
            )
            for client in clients
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении клиентов: {str(e)}")


@router.get('/get_schedules', status_code=200, response_model=List[ScheduleResponse])
async def get_schedules(date_range: DateRange = Depends()):
    """Получение расписания записей специалистов за указанный период."""
    try:
        start = date_range.start.astimezone(Settings.TIMEZONE) if date_range.start.tzinfo else date_range.start.replace(tzinfo=Settings.TIMEZONE)
        end = date_range.end.astimezone(Settings.TIMEZONE) if date_range.end.tzinfo else date_range.end.replace(tzinfo=Settings.TIMEZONE)
        
        to_dt_last_minute = end.replace(hour=23, minute=59)
        params = {
            'entityTypeId': constants.entityTypeId.appointment,
            'filter': {
                f'>={constants.uf.appointment.start}': start.isoformat(),
                f'<={constants.uf.appointment.end}': to_dt_last_minute.isoformat(),
            },
        }
        response = await BITRIX.get_all('crm.item.list', params)
        schedule_dict = {}
        logging.debug(f"\nITEM 0:\n{response}")
        for appointment in response:
            try:
                # Проверяем наличие всех необходимых полей
                if not all([
                    appointment.get('assignedById'),
                    appointment.get(constants.uf.appointment.start),
                    appointment.get(constants.uf.appointment.end),
                    appointment.get(constants.uf.appointment.patient),
                    appointment.get(constants.uf.appointment.code),
                    appointment.get(constants.uf.appointment.status)
                ]):
                    logging.debug(f"Пропуск записи с id={appointment.get('id')} из-за неполных данных")
                    continue

                specialist_id = appointment['assignedById']
                start_time = datetime.fromisoformat(appointment[constants.uf.appointment.start])
                start_of_day = start_time.replace(hour=3, minute=0, second=0, microsecond=0)
                end_time = datetime.fromisoformat(appointment[constants.uf.appointment.end])
                patient_id = appointment[constants.uf.appointment.patient]
                patient_type_id = (appointment[constants.uf.appointment.code] or [''])[0]
                patient_type = constants.listFieldValues.appointment.codeById.get(patient_type_id, '')
                raw_status = appointment[constants.uf.appointment.status]
                status = constants.listFieldValues.appointment.statusById.get(raw_status, '')

                # Пропускаем, если patient_type или status не найдены
                if not patient_type or not status:
                    logging.debug(f"Пропуск записи с id={appointment.get('id')} из-за некорректных patient_type или status")
                    continue

                appointment_obj = Appointment(
                    id=int(appointment['id']),
                    start=start_time,
                    end=end_time,
                    patient=Patient(id=int(patient_id), type=patient_type),
                    status=status
                )
                if specialist_id not in schedule_dict:
                    schedule_dict[specialist_id] = {}
                if start_of_day not in schedule_dict[specialist_id]:
                    schedule_dict[specialist_id][start_of_day] = []
                schedule_dict[specialist_id][start_of_day].append(appointment_obj)
            except (KeyError, ValueError, TypeError) as e:
                logging.debug(f"Пропуск записи с id={appointment.get('id')} из-за ошибки: {str(e)}")
                continue
        
        schedule_list = [
            ScheduleResponse(
                specialist_id=specialist_id,
                date=date,
                appointments=appointments
            )
            for specialist_id, dates in schedule_dict.items()
            for date, appointments in dates.items()
        ]
        return schedule_list
    except Exception as e:
        logging.error(f"Общая ошибка при получении расписания: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении расписания записей специалистов: {str(e)}")


@router.get('/get_work_schedules', status_code=200, response_model=List[WorkScheduleResponse])
async def get_work_schedules(date_range: DateRange = Depends()):
    """Получение рабочих расписаний специалистов за указанный период."""
    try:
        start = date_range.start.astimezone(Settings.TIMEZONE) if date_range.start.tzinfo else date_range.start.replace(tzinfo=Settings.TIMEZONE)
        end = date_range.end.astimezone(Settings.TIMEZONE) if date_range.end.tzinfo else date_range.end.replace(tzinfo=Settings.TIMEZONE)
        params = {
            'entityTypeId': constants.entityTypeId.workSchedule,
            'filter': {
                f'>={constants.uf.workSchedule.date}': start.isoformat(),
                f'<={constants.uf.workSchedule.date}': end.isoformat(),
            },
        }
        response = await BITRIX.get_all('crm.item.list', params)
        work_schedule_dict = {}
        for schedule in response:
            try:
                # Проверяем наличие всех необходимых полей
                if not all([
                    schedule.get('assignedById'),
                    schedule.get(constants.uf.workSchedule.date),
                    schedule.get(constants.uf.workSchedule.intervals)
                ]):
                    logging.debug(f"Пропуск расписания с id={schedule.get('id')} из-за неполных данных")
                    continue

                specialist_id = schedule['assignedById']
                date = datetime.fromisoformat(schedule[constants.uf.workSchedule.date])
                intervals = []
                raw_intervals = schedule[constants.uf.workSchedule.intervals] or []
                for interval in raw_intervals:
                    try:
                        start, end = interval.split(":")
                        intervals.append(WorkInterval(
                            start=datetime.fromtimestamp(float(start) / 1000).astimezone(Settings.TIMEZONE).isoformat(),
                            end=datetime.fromtimestamp(float(end) / 1000).astimezone(Settings.TIMEZONE).isoformat()
                        ))
                    except (ValueError, TypeError) as e:
                        logging.debug(f"Пропуск интервала в расписании с id={schedule.get('id')} из-за ошибки: {str(e)}")
                        continue

                # Пропускаем, если интервалы пустые
                if not intervals:
                    logging.debug(f"Пропуск расписания с id={schedule.get('id')} из-за отсутствия валидных интервалов")
                    continue

                work_schedule = WorkSchedule(id=schedule['id'], intervals=intervals)
                if specialist_id not in work_schedule_dict:
                    work_schedule_dict[specialist_id] = {}
                work_schedule_dict[specialist_id][date] = work_schedule
            except (KeyError, ValueError, TypeError) as e:
                logging.debug(f"Пропуск расписания с id={schedule.get('id')} из-за ошибки: {str(e)}")
                continue
        
        work_schedule_list = [
            WorkScheduleResponse(
                specialist_id=specialist_id,
                date=date,
                schedule=schedule
            )
            for specialist_id, dates in work_schedule_dict.items()
            for date, schedule in dates.items()
        ]
        return work_schedule_list
    except Exception as e:
        logging.error(f"Общая ошибка при получении рабочих расписаний: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении рабочих расписаний специалистов: {str(e)}")
        
@router.get('/get_deals', status_code=200)
async def get_deals():
    """Заглушка для получения сделок из Bitrix CRM."""
        # const deals = await this.bx.callListMethod('crm.deal.list', {'FILTER': filter});
        # console.log(deals);
        # return deals;
    pass
