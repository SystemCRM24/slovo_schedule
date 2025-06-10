from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timedelta
from functools import cached_property

from typing import Self


class AppointmentSet(BaseModel):
    type: str = Field(validation_alias='t')
    quantity: int = Field(validation_alias='q')
    duration: timedelta = Field(validation_alias='d', description="Время в минутах")

    @staticmethod
    def reduction_to_int(value: str) -> int:
        if value == "" or value is None:
            value = "0"
        return int(value)

    @field_validator('quantity', mode='before')
    @classmethod
    def quantity_validator(cls, value: str) -> int:
        return cls.reduction_to_int(value)
    
    @field_validator('duration', mode='before')
    def duration_validator(cls, value: str):
        return timedelta(minutes=cls.reduction_to_int(value))

    def is_valid(self):
        return all((self.type, self.quantity, self.duration))



class Stage(BaseModel):
    start: datetime
    duration: timedelta = Field(description='Время в неделях')
    sets: list[AppointmentSet] = Field(default_factory=list)

    @cached_property
    def end(self) -> datetime:
        return self.start + self.duration

    @classmethod
    def from_raw(cls, start: datetime, raw_stage: dict) -> Self:
        """Собираем объект из сырых данных"""
        duration = raw_stage.get('duration', "0")
        data = raw_stage.get('data', [])
        return cls(start=start, duration=duration, sets=data)
    
    @field_validator('duration', mode='before')
    @classmethod
    def duration_validator(cls, value: str) -> timedelta:
        return timedelta(weeks=int(value))
    
    @field_validator('sets', mode='before')
    @classmethod
    def sets_validator(cls, sets: list[dict]) -> list[AppointmentSet]:
        return [a for s in sets if (a := AppointmentSet(**s)).is_valid()]

    def is_valid(self) -> bool:
        return self.duration.days > 0 and len(self.sets) > 0
    
    def is_empty(self) -> bool:
        """Используется для определения пустой стадии, т.е. которую надо пропустить."""
        return self.duration.days == 0 and len(self.sets) == 0


class Deal(BaseModel):
    id: int = Field(validation_alias='ID')
    patient: int = Field(validation_alias='CONTACT_ID')

    model_config = ConfigDict(extra='ignore')
