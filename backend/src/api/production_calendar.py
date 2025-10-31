from fastapi import APIRouter, Depends
from datetime import date, timedelta
from src.schemas.api import RangeQuery
from src.core import BitrixClient


router = APIRouter(prefix='')


@router.get('/production_calendar')
async def get_production_calendar(query: RangeQuery = Depends()) -> list[date]:
    """Метод для получения производственного календаря. 
    Возращает массив строк, где каждая строка - дата без времени.
    Строится на основе каленадря битрикса id=3
    """
    raw_calendar = await BitrixClient.get_production_calendar()
    marked_holidays = raw_calendar.get('CALENDAR', {}).get('EXCLUSIONS', {})
    result = []
    while query.start <= query.end:
        year, month, day = map(str, (query.start.year, query.start.month, query.start.day))
        is_holiday = marked_holidays.get(year, {}).get(month, {}).get(day, None)
        if is_holiday is None:
            result.append(query.start)
        query.start += timedelta(days=1)
    return result
