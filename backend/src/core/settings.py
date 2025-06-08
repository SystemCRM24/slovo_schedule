from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pydantic import field_validator
from zoneinfo import ZoneInfo
from pathlib import Path


ROOT_PATH = Path(__file__).parent.parent.parent.parent


class _Settings(BaseSettings):
    MODE: str = 'dev'
    BITRIX_WEBHOOK: str
    DEFAULT_USER: int
    TIMEZONE: ZoneInfo = ZoneInfo('Europe/Moscow')

    model_config = ConfigDict(
        env_file = f"{ROOT_PATH}/.env",
        env_file_encoding = "utf-8",
        extra = "ignore"
    )

    @field_validator('TIMEZONE', mode='before')
    def parse_timezone(cls, v):
        if isinstance(v, str):
            return ZoneInfo(v)
        return ZoneInfo("Europe/Moscow")
    

Settings = _Settings()
