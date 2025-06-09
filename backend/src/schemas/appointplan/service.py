from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

from src.core import BXConstants
from src.utils import Interval


class BXSchedule(BaseModel):
    """Модель данных из битры"""
    id: int
    specialist: int = Field(validation_alias=BXConstants.schedule.uf.specialist)
    date: str | None = Field(validation_alias=BXConstants.schedule.uf.date)
    intervals: list[Interval] = Field(
        default_factory=list, 
        validation_alias=BXConstants.schedule.uf.intervals
    )

    model_config = ConfigDict(
        extra='ignore',
        arbitrary_types_allowed=True
    )

    @field_validator('intervals', mode='before')
    @classmethod
    def validate_intervals(cls, raw_intervals: list[str]) -> list[Interval]:
        intervals = []
        for raw_interval in raw_intervals:
            start, end = raw_interval.split(':')
            start, end = start[-13:], end[:13]
            intervals.append(Interval.from_js_timestamp(start, end))
        return intervals

    def is_valid(self):
        return all((self.date, len(self.intervals) > 0))


class BXAppointment(BaseModel):
    """Схема данных, которую ловим из битры"""
    id: int
    specialist: int = Field(validation_alias=BXConstants.appointment.uf.specialist)
    code: str | None = Field(validation_alias=BXConstants.appointment.uf.code)
    patient: int | None = Field(validation_alias=BXConstants.appointment.uf.patient)
    start: datetime | None = Field(validation_alias=BXConstants.appointment.uf.start)
    end: datetime | None = Field(validation_alias=BXConstants.appointment.uf.end)
    old_patient: int | None = Field(validation_alias=BXConstants.appointment.uf.old_patient)

    model_config = ConfigDict(extra='ignore')

    @field_validator('code', mode='before')
    @classmethod
    def code_validator(cls, value: list) -> str | None:
        if isinstance(value, list) and len(value) > 0:
            return BXConstants.appointment.lfv.codeById.get(value[0])
        return None
    
    @property
    def interval(self) -> Interval:
        return Interval(self.start, self.end)

    def is_valid(self) -> bool:
        return all((self.code, self.start, self.end, self.old_patient))
