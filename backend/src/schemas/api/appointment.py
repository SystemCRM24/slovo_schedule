from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

from src.core import BXConstants, Settings


class Appointment(BaseModel):
    """Договор для фронта."""
    id: int | None = None
    specialist: int
    patient: int
    start: str
    end: str
    code: str
    status: str | None = None

    def to_bx(self) -> dict:
        """Возвращает словарик, который можно отправить в битру"""
        auf = BXConstants.appointment.uf
        code = []
        code_id = BXConstants.appointment.lfv.idByCode.get(self.code, None)
        if code_id is not None:
            code.append(code_id)
        fields = {
            auf.specialist: self.specialist,
            auf.patient: self.patient,
            auf.start: self.start,
            auf.end: self.end,
            auf.code: code,
        }
        if self.status is not None:
            fields[auf.status] = BXConstants.appointment.lfv.idByStatus.get(self.status, None)
        return fields


class BXAppointment(BaseModel):
    """Схема данных, которую ловим из битры"""
    id: int
    specialist: int = Field(validation_alias=BXConstants.appointment.uf.specialist)
    patient: int | None = Field(validation_alias=BXConstants.appointment.uf.patient)
    start: str | None = Field(validation_alias=BXConstants.appointment.uf.start)
    end: str | None = Field(validation_alias=BXConstants.appointment.uf.end)
    code: str | None = Field(validation_alias=BXConstants.appointment.uf.code)
    status: str | None = Field(validation_alias=BXConstants.appointment.uf.status)
    abonnement: str | None = Field(validation_alias=BXConstants.appointment.uf.abonnement)

    # Значения для истории
    old_specialist: int | None = None
    old_patient: int | None = None
    old_start: str | None = None
    old_end: str | None = None
    old_code: str | None = None
    old_status: str | None = None

    # Настройки парсинга значений при создании модели.
    model_config = ConfigDict(extra='ignore')

    @field_validator('code', mode='before')
    @classmethod
    def code_validator(cls, value: list) -> str | None:
        if isinstance(value, list) and len(value) > 0:
            return BXConstants.appointment.lfv.codeById.get(value[0])
        return None
    
    @field_validator('status', mode='before')
    @classmethod
    def status_validator(cls, value) -> str | None:
        if isinstance(value, int):
            return BXConstants.appointment.lfv.statusById.get(value, None)
        return None
    
    @field_validator('abonnement', mode='before')
    @classmethod
    def abonnement_validator(cls, value) -> str:
        if value is None:
            return ""
        return value

    def is_valid(self) -> bool:
        return all((self.code, self.start, self.end, self.specialist, self.patient))
    
    def model_post_init(self, context):
        self.old_specialist = self.specialist
        self.old_patient = self.patient
        self.old_start = self.start
        self.old_end = self.end
        self.old_code = self.code
        self.old_status = self.status

    def parse_last_comment(self, comments: list[dict]) -> None:
        """Парсит комментарии с целью поиска коммента старых значений."""
        target = None
        for comment_item in comments:
            comment: str = comment_item.get('COMMENT', '')
            if comment.startswith('history;'):
                target = comment
                break
        if target is None:
            return
        try:
            values = target.split(';')
            # ['history', 'user_15', '30', '28.07.2025 09:00:00', '28.07.2025 10:00:00', 'L', 'Единичное', '197', '']
            old_specialst = int(values[1][5:])
            old_patient = int(values[2])
            old_start = self._parse_bx_date(values[3])
            old_end = self._parse_bx_date(values[4])
            old_code = values[5]
            old_status = values[6]
            self.old_specialist = old_specialst
            self.old_patient = old_patient
            self.old_start = old_start
            self.old_end = old_end
            self.old_code = old_code
            if old_status:
                self.old_status = old_status
        except:
            pass

    @staticmethod
    def _parse_bx_date(date: str) -> datetime:
        template = r'%d.%m.%Y %H:%M:%S'
        date_obj = datetime.strptime(date, template).replace(tzinfo=Settings.TIMEZONE)
        return date_obj.isoformat()


class AbonnementCancelDate(BaseModel):
    date: str
