from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkScheduleCreate(BaseModel):
    specialist: int = Field(..., description="ID специалиста")
    date: str = Field(..., description="Дата в формате ISO")
    intervals: List[str] = Field(..., description="Список интервалов, выраженный как список строк формата <timestamp>:<timestamp>")


class WorkSchedule(BaseModel):
    id: int
    specialist: int
    date: Optional[str]
    intervals: List[str]


class WorkScheduleCreateResponse(BaseModel):
    id: int