from datetime import datetime

from .settings import settings
from . import bitrix


class Handler:
    """Обрабатывает то, что нужно обработать"""

    def __init__(self, deal_id: str, user_id: str):
        self.deal_id = deal_id
        self.user_id = user_id
        self.date = datetime.now(settings.TIMEZONE)

    async def run(self) -> str:
        """Запускает процесс постановки приема"""
        await bitrix.get_specialist_from_code('R')
