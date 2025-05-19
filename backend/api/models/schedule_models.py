from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkScheduleCreate(BaseModel):
    specialist: int = Field(..., description="ID специалиста")
    date: str = Field(..., description="Дата в формате ISO (например, '2023-05-15')")
    intervals: List[str] = Field(..., description="Список интервалов")


class WorkSchedule(BaseModel):
    id: int
    specialist: int
    date: Optional[str]
    intervals: List[str]


class WorkScheduleCreateResponse(BaseModel):
    id: int