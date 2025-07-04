from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from functools import cached_property

from src.core import Settings


class RequestSchema(BaseModel):
    deal_id: int
    user_id: int
    start_date: datetime
    specialist_id: int = Field(alias='specialist')
    code: str
    duration: int
    qty: int

    @field_validator('start_date', mode='before')
    @classmethod
    def parse_start_date(cls, value: str) -> datetime:
        template = r'%d.%m.%Y %H:%M:%S'
        dt = datetime.strptime(value, template)
        return dt.replace(tzinfo=Settings.TIMEZONE)

    @field_validator('qty', mode='before')
    @classmethod
    def parse_qty(cls, value: str) -> int:
        if not value:
            value = '-1'
        return int(value)

    @cached_property
    def weekday(self) -> int:
        return self.start_date.weekday()
    
    @cached_property
    def time(self) -> tuple[int, int]:
        return self.start_date.hour, self.start_date.minute
