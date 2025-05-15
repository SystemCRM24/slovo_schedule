from fastapi import APIRouter
from datetime import datetime

from .appointment import router as appointment_router
from .schedule import router as schedule_router
from app.bitrix import BITRIX
from app.utils import BatchBuilder
from app.settings import Settings

from .constants import constants


router = APIRouter(prefix='/front', tags=['front'])

router.include_router(appointment_router)
router.include_router(schedule_router)


@router.get('/get_specialist', status_code=200)
async def get_specialist():
    response = await BITRIX.call(
        'user.get',
        {'@UF_DEPARTMENT': list(constants.departments.keys())},
        raw=True
    )
    specialists = {}
    for user in response['result']:
        name = user['LAST_NAME'] + " " + user['NAME'][0] + "."
        userDepratments = user['UF_DEPARTMENT'] or []
        departments = [constants.departments.get(str(d)) for d in userDepratments]
        specialists[user['ID']] = {'name': name, 'departments': departments}
    return specialists


@router.get('/get_clients', status_code=200)
async def get_clients():
    def parseClient(client):
        result[client['ID']] = client['NAME'] + (client['LAST_NAME'] if client['LAST_NAME'] else '')

    result = {}
    params = {
        'filter': {'TYPE_ID': "CLIENT"},
        'order': {'LAST_NAME': 'ASC', 'NAME': 'ASC'},
        'select': ['ID', 'NAME', 'LAST_NAME']
    }
    firstResponse = await BITRIX.call('crm.contact.list', params, raw=True)
    for client in firstResponse['result']:
        parseClient(client)
    current = firstResponse['next']
    total = firstResponse['total']
    requests = {}
    index = 0
    while current < total:
        params['start'] = current
        batch = BatchBuilder('crm.contact.list', params)
        requests[index] = batch.build()
        current += 50
        index += 1
        if index == 50:
            response = await BITRIX.call_batch({'halt': 0, 'cmd': requests})
            for page in response:
                for user in page:
                    parseClient(user)
            index = 0
            requests = {}
    return result


@router.get('/get_schedules', status_code=200)
async def get_schedules(start: datetime, end: datetime):
    toDtLastMinute = end.replace(hour=23, minute=59)
    params = {
        'entityTypeId': constants.entityTypeId.appointment,
        'filter': {
            f'>={constants.uf.appointment.start}': start.isoformat(),
            f'<={constants.uf.appointment.end}': toDtLastMinute.isoformat(),
        },
        # 'order': {constants.uf.appointment.start: 'ASC'}
    }
    response = await BITRIX.get_all('crm.item.list', params)
    schedule = {}
    for appointment in response:
        specialistId = appointment['assignedById']
        start = datetime.fromisoformat(appointment[constants.uf.appointment.start])
        startOfDay = start.replace(hour=3, minute=0, second=0, microsecond=0)
        end = datetime.fromisoformat(appointment[constants.uf.appointment.end])
        patientId = appointment[constants.uf.appointment.patient]
        patientTypeId = (appointment[constants.uf.appointment.code] or [''])[0]
        patientType = constants.listFieldValues.appointment.codeById[patientTypeId]
        rawStatus = appointment[constants.uf.appointment.status]
        status = constants.listFieldValues.appointment.statusById[rawStatus]
        # Наполняем объект
        specialistData = schedule.get(specialistId, None)
        if specialistData is None:
            specialistData = schedule[specialistId] = {}
        appointments: list = specialistData.get(startOfDay, None)
        if appointments is None:
            appointments = specialistData[startOfDay] = []
        appointments.append({
            'id': appointment['id'],
            'start': start,
            'end': end,
            'patient': {
                'id': patientId,
                'type': patientType
            },
            'status': status,
        })
    return schedule


@router.get('/get_work_schedules', status_code=200)
async def get_work_schedules(start: datetime, end: datetime):
    params = {
        'entityTypeId': constants.entityTypeId.workSchedule,
        'filter': {
            f'>={constants.uf.workSchedule.date}': start.isoformat(),
            f'<={constants.uf.workSchedule.date}': end.isoformat(),
        },
        # order: {[constants.uf.workSchedule.date]: 'ASC'}
    }
    response = await BITRIX.get_all('crm.item.list', params)
    workSchedule = {}
    for schedule in response:
        specialistData = workSchedule.get(schedule['assignedById'], None)
        if specialistData is None:
            specialistData = workSchedule[schedule['assignedById']] = {}
        date = datetime.fromisoformat(schedule[constants.uf.workSchedule.date])
        # date.setHours(0, 0, 0, 0);
        data = specialistData[date] = {
            'id': schedule['id'],
            'intervals': []
        }
        rawIntervals = schedule[constants.uf.workSchedule.intervals] or []
        for interval in rawIntervals: 
            start, end = interval.split(":")
            data['intervals'].append({
                'start': datetime.fromtimestamp(float(start) / 1000).astimezone(Settings.TIMEZONE).isoformat(), 
                'end': datetime.fromtimestamp(float(end) / 1000).astimezone(Settings.TIMEZONE).isoformat()
            });
    return workSchedule


@router.get('/get_deals', status_code=200)
async def get_deals():
        # const deals = await this.bx.callListMethod('crm.deal.list', {'FILTER': filter});
        # console.log(deals);
        # return deals;
    pass
