from pydantic_settings import BaseSettings
from pydantic import field_validator
from zoneinfo import ZoneInfo
from pathlib import Path


class Settings(BaseSettings):
    BITRIX_WEBHOOK: str
    TIMEZONE: ZoneInfo = ZoneInfo('Europe/Moscow')

    class Config:
        env_file = Path(__file__).parent.parent.parent.parent
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator('TIMEZONE', mode='before')
    def parse_timezone(cls, v):
        if isinstance(v, str):
            return ZoneInfo(v)
        return ZoneInfo("Europe/Moscow")
    

settings = Settings()
