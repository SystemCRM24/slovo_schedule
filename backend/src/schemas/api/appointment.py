from pydantic import BaseModel, Field
from typing import Optional, Self

from src.core import BXConstants


class Appointment(BaseModel):
    id: Optional[int] = Field(description="ID смарт процесса, ваш капитан.")
    specialist: int = Field(escription="ID специалиста")
    code: str = Field(description="Код записи (например, 'L', 'A')")
    patient: int = Field(description="ID пациента")
    start: str = Field(description="Время начала в формате ISO")
    end: str = Field(description="Время окончания в формате ISO")
    history_client: int = Field(description="ID изначального ребенка")
    

    @classmethod
    def from_bitrix(cls, data: dict) -> Self:
        code_ids_list = data.get(BXConstants.appointment.uf.code, None)
        print(data)
        return cls(
            id=data.get('id', None),
            specialist=data.get(BXConstants.appointment.uf.specialist, None),

        )


{
    'id': 34, 
    'ufCrm3Children': '8', 
    'ufCrm3StartDate': '2025-05-06T09:00:00+03:00', 
    'ufCrm3EndDate': '2025-05-06T10:00:00+03:00', 
    'ufCrm3Status': 50, 
    'ufCrm3Code': ['52'], 
    'ufCrm3HistoryClient': '20', 
    'assignedById': 8, 
}

# class AppointmentCreate(BaseModel):
#     specialist: int = Field(..., description="ID специалиста")
#     patient: int = Field(..., description="ID пациента")
#     start: str = Field(..., description="Время начала в формате ISO")
#     end: str = Field(..., description="Время окончания в формате ISO")
#     code: str = Field(..., description="Код записи (например, 'L', 'A')")

#     @validator("code")
#     def validate_code(cls, v):
#         if v not in constants.listFieldValues.appointment.idByCode:
#             raise ValueError("Недопустимый код")
#         return v


# class Appointment(BaseModel):
#     id: int
#     specialist: int
#     patient: Optional[int]
#     start: Optional[str]
#     end: Optional[str]
#     code: str

#     @classmethod
#     def from_bitrix(cls, data: dict) -> "Appointment":
#         raw_code = data.get(constants.uf.appointment.code)
#         code_value = raw_code[0] if isinstance(raw_code, list) and raw_code else raw_code
#         return cls(
#             id=data["id"],
#             specialist=data["assignedById"],
#             patient=data.get(constants.uf.appointment.patient),
#             start=data.get(constants.uf.appointment.start),
#             end=data.get(constants.uf.appointment.end),
#             code=constants.listFieldValues.appointment.codeById.get(
#                 code_value, "unknown"
#             ),
#         )


# class AppointmentCreateResponse(BaseModel):
#     id: int