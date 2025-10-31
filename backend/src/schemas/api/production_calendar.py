from pydantic import BaseModel
from datetime import date


class RangeQuery(BaseModel):
    """Модель для парсинга дат для запроса по рабочему календарю"""
    start: date
    end: date
