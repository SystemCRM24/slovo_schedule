from pydantic import BaseModel, Field, validator
from typing import List, Optional
from ..constants import constants


class AppointmentCreate(BaseModel):
    specialist: int = Field(..., description="ID специалиста")
    patient: int = Field(..., description="ID пациента")
    start: str = Field(..., description="Время начала в формате ISO")
    end: str = Field(..., description="Время окончания в формате ISO")
    status: str = Field(
        ..., description="Статус записи (например, 'booked', 'confirmed')"
    )
    code: str = Field(..., description="Код записи (например, 'L', 'A')")

    @validator("status")
    def validate_status(cls, v):
        if v not in constants.listFieldValues.appointment.idByStatus:
            raise ValueError("Недопустимый статус")
        return v

    @validator("code")
    def validate_code(cls, v):
        if v not in constants.listFieldValues.appointment.idByCode:
            raise ValueError("Недопустимый код")
        return v


class Appointment(BaseModel):
    id: int
    specialist: int
    patient: Optional[int]
    start: Optional[str]
    end: Optional[str]
    status: str
    code: str

    @classmethod
    def from_bitrix(cls, data: dict) -> "Appointment":
        raw_code = data.get(constants.uf.appointment.code)
        code_value = raw_code[0] if isinstance(raw_code, list) and raw_code else raw_code
        return cls(
            id=data["id"],
            specialist=data["assignedById"],
            patient=data.get(constants.uf.appointment.patient),
            start=data.get(constants.uf.appointment.start),
            end=data.get(constants.uf.appointment.end),
            status=constants.listFieldValues.appointment.statusById.get(
                data.get(constants.uf.appointment.status), "unknown"
            ),
            code=constants.listFieldValues.appointment.codeById.get(
                code_value, "unknown"
            ),
        )


class AppointmentCreateResponse(BaseModel):
    id: int