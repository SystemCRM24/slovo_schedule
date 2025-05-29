from pydantic import BaseModel, Field, model_validator
from typing import List, Dict

class AppointmentSchema(BaseModel):
    type: str = Field(alias='t')
    quantity: int = Field(alias='q')
    duration: int = Field(alias='d')

class StageSchema(BaseModel):
    duration: int
    data: List[AppointmentSchema]

    @model_validator(mode='before')
    def filter_valid_appointments(cls, values):
        data = values.get('data', [])
        filtered = [
            item for item in data
            if str(item.get('q', '')).strip() and str(item.get('d', '')).strip()
        ]
        values['data'] = filtered
        return values

class RequestSchema(BaseModel):
    deal_id: int
    user_id: int
    start_date: str
    data: Dict[str, StageSchema]  # first_stage, second_stage, и всякое другое


class RequestSchemaV2(BaseModel):
    deal_id: int
    user_id: int
    data: Dict[str, StageSchema]  # first_stage, second_stage, и всякое другое
