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
