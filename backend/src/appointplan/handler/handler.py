import traceback
import asyncio
import json
from datetime import datetime, timedelta

from src.core import Settings
from src.logger import logger
from src.middleware import AppExceptionHandlerMiddleware as AEHM
from src.appointplan.service import AppointplanException
from src.schemas.appointplan import Stage, AppointmentSet


class Handler:

    def __init__(self, request: str):
        self.request = request                  # Сырой запрос
        self.deal: dict = None                  # Инфа по сделке
        self.users = [Settings.DEFAULT_USER]    # Cписок пользвателей, кому будет отправлены уведомления
        self.stages = []                        # Стадии, занятия в которых нужно распланировать
        self.departments: dict = {}             # Подразделения по типу
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
        """Непосредственно, сама работа обработчика"""
        context = ContextFiller(self)
        await context.fill()

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


class ContextFiller:
    """Определяет контекст выполнения для обработчика"""

    __slots__ = ('handler', 'data')

    stage_names = ('first_stage', 'second_stage')

    def __init__(self, handler: Handler):
        self.handler = handler
        self.data: dict = None

    async def fill(self):
        self.data = json.loads(self.handler.request)
        await asyncio.gather(
            self.fill_deal_info(),
            self.fill_departments_info(),
            self.fill_user_id(),
            self.fill_stages()
        )

    async def fill_deal_info(self):
        """Заполняет обработчик инфой о сделке, из которой поступил запрос."""
    
    async def fill_departments_info(self):
        """Заполняет обработчик информации о подразделениях, специалистах, их графике работы и рассписании."""
            
    async def fill_user_id(self):
        """Заполняет обработчик инфой о пользвателе, которому нужно отправить сообщение."""
        user_id = self.data.get('user_id', None)
        if user_id:
            self.handler.users.append(user_id)

    async def fill_stages(self):
        """Заполняет обработчик стадиями. Фильтрует их и занятия внутри."""
        try:
            start = datetime.fromisoformat(self.data.get('start_date', None))
        except ValueError:
            logger.warning("Failed to retrieve start date from the request. Using tommorrow's date instead.")
            start = datetime.now(Settings.TIMEZONE) + timedelta(days=1)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        for stage_name in self.stage_names:
            raw_stage: dict = self.data.get(stage_name, None)
            if raw_stage is None:
                continue
            stage = Stage.from_raw(start, raw_stage)
            if stage.is_empty():
                continue
            if not stage.is_valid():
                print(stage)
                raise AppointplanException(f"Данные по {stage_name} заполнены некорректно.")
            self.handler.stages.append(stage)
            start = stage.end
