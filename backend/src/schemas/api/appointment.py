from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Self

from src.core import BXConstants


class Appointment(BaseModel):
    """Договор для фронта."""
    id: int | None = None
    specialist: int
    code: str
    patient: int
    start: str
    end: str
    old_patient: int

    def to_bx(self) -> dict:
        """Возвращает словарик, который можно отправить в битру"""
        auf = BXConstants.appointment.uf
        code = []
        code_id = BXConstants.appointment.lfv.idByCode.get(self.code, None)
        if code_id is not None:
            code.append(code_id)
        return {
            auf.specialist: self.specialist,
            auf.code: code,
            auf.patient: self.patient,
            auf.start: self.start,
            auf.end: self.end,
            auf.old_patient: self.old_patient
        }


class BXAppointment(BaseModel):
    """Схема данных, которую ловим из битры"""
    id: int
    specialist: int = Field(validation_alias=BXConstants.appointment.uf.specialist)
    code: str | None = Field(validation_alias=BXConstants.appointment.uf.code)
    patient: int | None = Field(validation_alias=BXConstants.appointment.uf.patient)
    start: str | None = Field(validation_alias=BXConstants.appointment.uf.start)
    end: str | None = Field(validation_alias=BXConstants.appointment.uf.end)
    old_patient: int | None = Field(validation_alias=BXConstants.appointment.uf.old_patient)

    model_config = ConfigDict(extra='ignore')

    @field_validator('code', mode='before')
    @classmethod
    def code_validator(cls, value: list) -> str | None:
        if isinstance(value, list) and len(value) > 0:
            return BXConstants.appointment.lfv.codeById.get(value[0])
        return None

    def is_valid(self) -> bool:
        return all((self.code, self.start, self.end,self.old_patient))
