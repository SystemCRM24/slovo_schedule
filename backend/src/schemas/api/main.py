from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

from src.core import BXConstants


class BXSpecialist(BaseModel):
    id: int = Field(validation_alias='ID')
    first_name: str = Field(validation_alias='NAME', exclude=True)
    last_name: str = Field(validation_alias='LAST_NAME', exclude=True)
    departments: list[str] = Field(validation_alias='UF_DEPARTMENT')
    sort_index: int = Field(validation_alias='UF_USR_1750081359137')

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
    
    @field_validator('sort_index', mode='before')
    @classmethod
    def sort_index_validator(cls, value: int | None) -> int:
        if not isinstance(value, int):
            return 666_666_666
        return int(value)

    @computed_field
    def name(self) -> str:
        """Возвращает полное имя"""
        last_name = self.last_name.strip() if self.last_name else ""
        first_name = f' {self.first_name[0]}.' if self.first_name else ""
        return f'{last_name}{first_name}'


class BXClient(BaseModel):
    id: int = Field(validation_alias='ID')
    name: str = Field(validation_alias='NAME', exclude=True)
    last_name: str = Field(validation_alias='LAST_NAME', exclude=True)

    @field_validator('last_name', mode='before')
    @classmethod
    def last_name_validator(cls, value) -> str:
        if isinstance(value, str):
            return value
        return ''

    @computed_field
    def full_name(self) -> str:
        name = self.name
        if self.last_name:
            name = f'{self.name} {self.last_name}'
        return name


class QueryDateRange(BaseModel):
    start: str
    end: str
