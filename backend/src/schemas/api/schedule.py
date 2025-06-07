from pydantic import BaseModel, Field, ConfigDict

from src.core import BXConstants


class Schedule(BaseModel):
    """Договор для фронта"""
    id: int | None
    specialist: int
    date: str
    intervals: list[str]

    def to_bx(self) -> dict:
        suf = BXConstants.schedule.uf
        return {
            suf.specialist: self.specialist,
            suf.date: self.date,
            suf.intervals: self.intervals
        }


class BXSchedule(BaseModel):
    """Модель данных из битры"""
    id: int
    specialist: int = Field(validation_alias=BXConstants.schedule.uf.specialist)
    date: str | None = Field(validation_alias=BXConstants.schedule.uf.date)
    intervals: list[str] = Field(
        default_factory=list, 
        validation_alias=BXConstants.schedule.uf.intervals
    )

    model_config = ConfigDict(extra='ignore')

    def is_valid(self):
        return all((self.date, len(self.intervals) > 0))
