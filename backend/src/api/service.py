from src.schemas.api import Schedule, BXSchedule
from datetime import datetime, timedelta, date
from src.core import Settings, BitrixClient, BXConstants
from src.utils import BatchBuilder
import holidays
import asyncio


RU_HOLIDAYS = holidays.country_holidays('RU', years=[2025, 2026, 2027])

get_params = lambda f: {"entityTypeId": BXConstants.schedule.entityTypeId, "fields": f}


async def create_schedule_massive(schedule: Schedule) -> list[BXSchedule]:
    """Создает графики специалиста на 1 год по шаблону schedule."""
    date = datetime.fromisoformat(schedule.date).replace(tzinfo=Settings.TIMEZONE)
    existed_schedules = await get_schedules(schedule.specialist, date)
    to_delete = set()
    builder = BatchBuilder('crm.item.add')
    batches = {}
    intervals = list(map(lambda x: list(map(int, x.split(':'))), schedule.intervals))
    for q in range(52):
        if date not in RU_HOLIDAYS:
            existed_schedule = existed_schedules.get(date.date(), None)
            if existed_schedule is not None:
                to_delete |= existed_schedule
            s = Schedule(
                specialist=schedule.specialist,
                date=date.isoformat(),
                intervals=[':'.join(map(str, i)) for i in intervals]
            )
            builder.params = get_params(s.to_bx())
            batches[f'batch{q}'] = builder.build()
        date = date + timedelta(weeks=1)
        for interval in intervals:
            interval[0] += 604800000
            interval[1] += 604800000
    response: dict[str, dict] = await BitrixClient.call_batch(batches)
    result = [BXSchedule.model_validate(i.get('item', {})) for i in response.values()]
    asyncio.create_task(delete_schedules(to_delete))
    return result


async def get_schedules(specialist_id: str | int, date: datetime) -> dict[date, set[str | int]]:
    """Получает графики специалиста, которые могут наслоится на новые."""
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = date.replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(weeks=53)
    response = await BitrixClient.get_specialists_schedules(
        start=start.isoformat(), end=end.isoformat(), spec_ids=(specialist_id, )
    )
    result = {}
    for schedule in response:
        schedule_date = date.fromisoformat(schedule.get('ufCrm4Date')).date()
        if schedule_date not in result:
            result[schedule_date] = set()
        result[schedule_date].add(schedule.get('id'))
    return result


async def delete_schedules(schedule_ids: set[str | int]) -> None:
    """Удаление существующих графиков."""
    seti = BXConstants.schedule.entityTypeId
    for _id in schedule_ids:
        await BitrixClient.delete_crm_item(seti, _id)
