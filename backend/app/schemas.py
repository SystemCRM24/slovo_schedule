from pydantic import BaseModel, Field


class AppointmentSchema(BaseModel):
    """Схема занятия"""
    type: str = Field(alias='t')
    quantity: int = Field(alias='q')
    duration: int = Field(alias='d')


class RequestShema(BaseModel):
    """Схема запроса для создания занятий"""
    deal_id: int
    user_id: int | None = None
    data: list[AppointmentSchema] = Field(default_factory=list)
