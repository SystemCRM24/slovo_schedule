from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from functools import cached_property

from typing import Self


class AppointmentSet(BaseModel):
    type: str = Field(validation_alias='t')
    quantity: int = Field(validation_alias='q')
    duration: int = Field(validation_alias='d')

    @field_validator('quantity', 'duration', mode='before')
    @classmethod
    def empty_string_validator(cls, value: str) -> int:
        if value == "":
            value = "0"
        return int(value)

    def is_valid(self):
        return all((self.type, self.quantity, self.duration))



class Stage(BaseModel):
    start: datetime
    duration: int
    sets: list[AppointmentSet] = Field(default_factory=list)

    @cached_property
    def end(self) -> datetime:
        return self.start + timedelta(weeks=self.duration)

    @classmethod
    def from_raw(cls, start: datetime, raw_stage: dict) -> Self:
        """Собираем объект из сырых данных"""
        duration = raw_stage.get('duration', "0")
        data = raw_stage.get('data', [])
        return cls(start=start, duration=duration, sets=data)
    
    @field_validator('duration', mode='before')
    @classmethod
    def duration_validator(cls, value: str) -> int:
        return int(value)
    
    @field_validator('sets', mode='before')
    @classmethod
    def sets_validator(cls, sets: list[dict]) -> list[AppointmentSet]:
        return [a for s in sets if (a := AppointmentSet(**s)).is_valid()]

    def is_valid(self) -> bool:
        return self.duration > 0 and len(self.sets) > 0
    
    def is_empty(self) -> bool:
        """Используется для определения пустой стадии, т.е. которую надо пропустить."""
        return self.duration == 0 and len(self.sets) == 0
