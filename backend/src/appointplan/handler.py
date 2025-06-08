import traceback
import asyncio

from src.core import Settings
from src.logger import logger
from src.middleware import AppExceptionHandlerMiddleware as AEHM
from .service import AppointplanException


class Handler:

    def __init__(self, response: str):
        self.response = response                # Сырой запрос
        self.deal: dict = None                  # Инфа по сделке
        self.user_id = Settings.DEFAULT_USER    # Пользователь, которому отсылаем сообщения
        self.stages = []                        # Стадии, занятия в которых нужно распланировать
        self.departments: dict = None           # Подразделения по типу
        self.message = None                     # Сообщение, которое пошлем пользователю
        self.appointments = []                  # Расставленные занятия

    async def run(self):
        """Проставляем занятия и отправляем сообщение. Обернуто в транзакцию."""
        try:
            await self._run()
            self.message = "Занятия были расставлены успешно."
        except AppointplanException as app_exc:
            self.message = str(AppointplanException)
            logger.error(self.message)
        except Exception as e:
            message = str(e)
            stack = traceback.extract_stack()
            trace_format = traceback.format_exc()
            AEHM._log_app_exception(stack, trace_format)
        asyncio.create_task(self.send_message())
        return await send_appointments()
    
    async def _run(self):
        pass
    
    async def send_message(self):
        """Посылает сообщение пользователю в битру"""
        # logger.info('Message was sent')
        logger.warning('Метод отправки сообщений не написан.')
        logger.info(f"Сообщение: {self.message}")
    
    async def send_appointments(self):
        """Посылает батч-запрос на расстановку занятий в битру."""
        # logger.info('The appointments were scheduled.')
        logger.warning('Метод отправки занятий в битру не написан.')
        logger.info(f'Занятия для отправки:\n' + '\n'.join(self.appointments))
    
    def parse_data(self):
        pass

    async def create_context(self):
        pass

