from fastapi import APIRouter
from datetime import datetime

from .appointment import router as appointment_router
from .schedule import router as schedule_router
from app.bitrix import BITRIX
from app.utils import BatchBuilder

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
    # const toDtLastMinute = getDateWithTime(to, 23, 59);
    #     const params = {
    #         entityTypeId: constants.entityTypeId.appointment,
    #         filter: {
    #             [`>=${constants.uf.appointment.start}`]: from,
    #             [`<=${constants.uf.appointment.end}`]: toDtLastMinute,
    #         },
    #         order: {[constants.uf.appointment.start]: 'ASC'}
    #     }
    #     const response = await this.bx.callListMethod('crm.item.list', params);
    #     const schedule = {};
    #     for (const itemsObject of response) {
    #         for (const appointment of itemsObject.items) {
    #             const specialistId = appointment.assignedById;
    #             const start = new Date(appointment[constants.uf.appointment.start]);
    #             const startOfDay = new Date(start);
    #             startOfDay.setHours(3, 0, 0, 0);
    #             const end = new Date(appointment[constants.uf.appointment.end]);
    #             const patientId = appointment[constants.uf.appointment.patient];
    #             const patientTypeId = (appointment[constants.uf.appointment.code] || [''])[0];
    #             const patientType = constants.listFieldValues.appointment.codeById[patientTypeId];
    #             const rawStatus = appointment[constants.uf.appointment.status];
    #             const status = constants.listFieldValues.appointment.statusById[rawStatus];
    #             // Наполняем объект
    #             const specialistData = schedule[specialistId] ??= {};
    #             const appointments = specialistData[startOfDay] ??= [];
    #             appointments.push({
    #                 id: appointment.id,
    #                 start,
    #                 end,
    #                 patient: {
    #                     id: patientId,
    #                     type: patientType
    #                 },
    #                 status,
    #             });
    #         }
    #     }
    #     return schedule;
    pass


@router.get('/get_work_schedules', status_code=200)
async def get_work_schedules(start: datetime, end: datetime):
    # const params = {
    #         entityTypeId: constants.entityTypeId.workSchedule,
    #         filter: {
    #             [`>=${constants.uf.workSchedule.date}`]: from,
    #             [`<=${constants.uf.workSchedule.date}`]: to,
    #         },
    #         order: {[constants.uf.workSchedule.date]: 'ASC'}
    #     }
    #     const response = await this.bx.callListMethod('crm.item.list', params);
    #     const workSchedule = {};
    #     for (const items of response) {
    #         for (const schedule of items.items) {
    #             const specialistData = workSchedule[schedule.assignedById] ??= {};
    #             const date = new Date(schedule[constants.uf.workSchedule.date]);
    #             // date.setHours(0, 0, 0, 0);
    #             const data = specialistData[date] = {
    #                 id: schedule.id,
    #                 intervals: []
    #             };
    #             const rawIntervals = schedule[constants.uf.workSchedule.intervals] || [];
    #             for (const interval of rawIntervals) {
    #                 const [start, end] = interval.split(":");
    #                 data.intervals.push({start: new Date(parseInt(start)), end: new Date(parseInt(end))});
    #             }
    #         }
    #     }
    #     return workSchedule;
    pass


@router.get('/get_deals', status_code=200)
async def get_deals():
        #     const deals = await this.bx.callListMethod('crm.deal.list', {'FILTER': filter});
        # console.log(deals);
        # return deals;
    pass
