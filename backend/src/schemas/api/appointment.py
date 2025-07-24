from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    # Значения для истории
    old_specialist: int | None = Field(validation_alias=BXConstants.appointment.uf.old_specialist)
    old_patient: int | None = Field(validation_alias=BXConstants.appointment.uf.old_patient)
    old_start: str | None = Field(validation_alias=BXConstants.appointment.uf.old_start)
    old_end: str | None = Field(validation_alias=BXConstants.appointment.uf.old_end)
    old_code: str | None = Field(validation_alias=BXConstants.appointment.uf.old_code)

    model_config = ConfigDict(extra='ignore')

    @field_validator('code', mode='before')
    @classmethod
    def code_validator(cls, value: list) -> str | None:
        if isinstance(value, list) and len(value) > 0:
            return BXConstants.appointment.lfv.codeById.get(value[0])
        return None
    
    @field_validator('old_code', mode='before')
    @classmethod
    def old_code_validator(cls, value: int) -> str | None:
        if isinstance(value, int):
            return BXConstants.appointment.lfv.oldCodeById.get(str(value))
        return None

    def is_valid(self) -> bool:
        return all((self.code, self.start, self.end,self.old_patient))

