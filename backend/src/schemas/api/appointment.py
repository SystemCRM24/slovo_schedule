from pydantic import BaseModel, Field
from typing import Optional, Self

from src.core import BXConstants


class Appointment(BaseModel):
    id: Optional[int] = Field(default=None, description="ID смарт процесса, ваш капитан.")
    specialist: Optional[int] = Field(default=None, escription="ID специалиста")
    code: Optional[str] = Field(default=None, description="Код записи (например, 'L', 'A')")
    patient: Optional[int] = Field(default=None, description="ID пациента")
    start: Optional[str] = Field(default=None, description="Время начала в формате ISO")
    end: Optional[str] = Field(default=None, description="Время окончания в формате ISO")
    old_patient: Optional[int] = Field(default=None, description="ID изначального ребенка")

    @classmethod
    def from_bitrix(cls, data: dict) -> Self:
        """На основе словаря из битры создаем объект"""
        app_uf = BXConstants.appointment.uf
        obj = cls()
        id = data.get('id')
        if id is not None:
            obj.id = id
        specialist = data.get(app_uf.specialist)
        if specialist is not None:
            obj.specialist = specialist
        code_ids_list = data.get(app_uf.code)
        if isinstance(code_ids_list, list) and len(code_ids_list) > 0:
            obj.code = BXConstants.appointment.lfv.codeById.get(code_ids_list[0])
        patient = data.get(app_uf.patient, "")
        if patient is not None and patient.isdigit():
            obj.patient = int(patient)
        start = data.get(app_uf.start)
        if start is not None:
            obj.start = start
        end = data.get(app_uf.end)
        if end is not None:
            obj.end = end
        old_patient = data.get(app_uf.old_patient)
        if old_patient is not None and old_patient.isdigit():
            obj.old_patient = int(old_patient)
        return obj
    
    def to_bitrix(self) -> dict:
        """На сонове объекта создаем словарь для битры"""
        app_uf = BXConstants.appointment.uf
        code = []
        code_id = BXConstants.appointment.lfv.idByCode.get(self.code, None)
        if code_id is not None:
            code.append(code_id)
        return {
            app_uf.specialist: self.specialist,
            app_uf.code: code,
            app_uf.patient: self.patient,
            app_uf.start: self.start,
            app_uf.end: self.end,
            app_uf.old_patient: self.old_patient
        }
