from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

from src.core import BXConstants


class BXSpecialist(BaseModel):
    id: int = Field(validation_alias='ID')
    first_name: str = Field(validation_alias='NAME', exclude=True)
    last_name: str = Field(validation_alias='LAST_NAME', exclude=True)
    departments: list[str] = Field(validation_alias='UF_DEPARTMENT')

    model_config = ConfigDict(extra='ignore')

    @field_validator('departments', mode='before')
    @classmethod
    def departments_validator(cls, value: list[int]) -> list[str]:
        """Преобразовывает в буквенный код"""
        codes = []
        for department_id in value:
            code = BXConstants.departments.get(str(department_id), None)
            if code is not None:
                codes.append(code)
        return codes

    @computed_field
    def name(self) -> str:
        """Возвращает полное имя"""
        return f'{self.last_name.strip()} {self.first_name[0]}.'
