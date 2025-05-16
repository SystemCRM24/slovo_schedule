from datetime import datetime
import logging
from typing import List, Optional
from pydantic import BaseModel, Field


class Interval(BaseModel):
    start: str = Field(
        ...,
        description="Время начала интервала в формате ISO (например, '2023-05-15T10:00:00')",
    )
    end: str = Field(
        ...,
        description="Время окончания интервала в формате ISO (например, '2023-05-15T11:00:00')",
    )


class WorkScheduleCreate(BaseModel):
    specialist: int = Field(..., description="ID специалиста")
    date: str = Field(..., description="Дата в формате ISO (например, '2023-05-15')")
    intervals: List[Interval] = Field(..., description="Список интервалов")


class WorkSchedule(BaseModel):
    id: int
    specialist: int
    date: Optional[str]
    intervals: List[Interval]


class WorkScheduleCreateResponse(BaseModel):
    id: int
    title: str
    createdTime: str
    assignedById: int
    date: Optional[str]  # ufCrm4Date
    intervals: List[Interval]  # ufCrm4Intervals
    categoryId: Optional[int]
    createdBy: Optional[int]
    updatedBy: Optional[int]

    @classmethod
    def from_bitrix(cls, data: dict) -> "WorkScheduleCreateResponse":
        intervals = []
        raw_intervals = data.get("ufCrm4Intervals", [])
        for interval_str in raw_intervals:
            # Ожидаем формат: "1747029600000:1747040400000"
            try:
                start_ms, end_ms = map(int, interval_str.split(":"))
                start = datetime.fromtimestamp(start_ms / 1000).strftime("%Y-%m-%dT%H:%M:%S+03:00")
                end = datetime.fromtimestamp(end_ms / 1000).strftime("%Y-%m-%dT%H:%M:%S+03:00")
                intervals.append(Interval(start=start, end=end))
            except ValueError as e:
                logging.error(f"Ошибка парсинга интервала {interval_str}: {e}")
                continue

        return cls(
            id=data["id"],
            title=data["title"],
            createdTime=data["createdTime"],
            assignedById=data["assignedById"],
            date=data.get("ufCrm4Date"),
            intervals=intervals,
            categoryId=data.get("categoryId"),
            createdBy=data.get("createdBy"),
            updatedBy=data.get("updatedBy"),
        )