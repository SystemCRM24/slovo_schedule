from fastapi import APIRouter, Depends
from datetime import date, timedelta
from src.schemas.api import RangeQuery
from src.core import BitrixClient


router = APIRouter(prefix='')


@router.get('/get_holidays')
async def get_holidays(query: RangeQuery = Depends()) -> list[date]:
    """Метод для получения списка выходных, основанном на производственном календаре"""
    raw_calendar = await BitrixClient.get_production_calendar()
    marked_holidays = raw_calendar.get('CALENDAR', {}).get('EXCLUSIONS', {})
    result = []
    while query.start <= query.end:
        year, month, day = map(str, (query.start.year, query.start.month, query.start.day))
        is_holiday = marked_holidays.get(year, {}).get(month, {}).get(day, None)
        if is_holiday is not None:
            result.append(query.start)
        query.start += timedelta(days=1)
    return result
