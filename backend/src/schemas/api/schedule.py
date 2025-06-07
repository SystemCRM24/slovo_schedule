from datetime import datetime
from typing import Self
from pydantic import BaseModel, Field

from src.core import BXConstants


class Schedule(BaseModel):
    id: int | None = Field(default=None)
    specialist: int | None = Field(default=None, description="ID специалиста")
    date: str | None = Field(default=None, description="Дата в формате ISO")
    intervals: list[str] = Field(
        default_factory=list,
        description="Список интервалов, выраженный как список строк формата <timestamp>:<timestamp>"
    )

    @classmethod
    def from_bitrix(cls, data: dict) -> Self:
        """На основе словаря из битры создаем объект"""
            
        sch_uf = BXConstants.schedule.uf
        obj = cls()
        id = data.get('id')
        if id is not None:
            obj.id = id
        specialist = data.get(sch_uf.specialist)
        if specialist is not None:
            obj.specialist = specialist
        date = data.get(sch_uf.date, None)
        if date is not None:
            obj.date = date
        intervals = data.get(sch_uf.intervals)
        if isinstance(intervals, list):
            obj.intervals = intervals
        return obj
