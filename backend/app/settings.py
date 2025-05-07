from pydantic_settings import BaseSettings
from pydantic import field_validator
from zoneinfo import ZoneInfo


class UserFields:
    code = "UF_CRM_6800C01983990"
    duration = "UF_CRM_1746625717138"


class Settings(BaseSettings):
    BITRIX_WEBHOOK: str
    TIMEZONE: ZoneInfo = ZoneInfo('Europe/Moscow')

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator('TIMEZONE', mode='before')
    def parse_timezone(cls, v):
        if isinstance(v, str):
            return ZoneInfo(v)
        return ZoneInfo("Europe/Moscow")
    


settings = Settings()
