from datetime import datetime

from .settings import settings


class Handler:
    """Обрабатывает то, что нужно обработать"""

    def __init__(self, deal_id: str, user_id: str):
        self.deal_id = deal_id
        self.user_id = user_id
        self.date = datetime.now(settings.TIMEZONE)

    async def run(self) -> str:
        """Запускает процесс постановки приема"""