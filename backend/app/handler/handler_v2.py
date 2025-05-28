from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
from app.settings import Settings
from app.schemas import RequestSchema
from app import bitrix
from app.utils import BatchBuilder
from api.constants import constants
from .specialist import Specialist

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HandlerV2:
    def __init__(self, data: RequestSchema):
        """
        Инициализация обработчика для распределения занятий.

        Args:
            data (RequestSchema): Входные данные с информацией о сделке, пользователе и этапах.
        """
        self.initial_time = datetime.now(Settings.TIMEZONE) + timedelta(days=1)
        self.data = data
        self.specialists = self.create_specialists()
        self.total_required = sum(
            appoint.quantity
            for stage in self.data.data.values()
            for appoint in stage.data
        )
        self.min_break = 15  # Минимальный перерыв между занятиями в минутах
        self.max_break = 45  # Максимальный перерыв между занятиями в минутах
        logger.info(
            f"Инициализирован Handler для deal_id={self.data.deal_id}, user_id={self.data.user_id}, "
            f"всего занятий={self.total_required}"
        )

    def create_specialists(self) -> Tuple[Specialist]:
        """
        Создает список объектов Specialist для каждого типа занятия.

        Returns:
            Tuple[Specialist]: Кортеж объектов Specialist.
        """
        specialists = []
        for stage in self.data.data.values():
            for d in stage.data:
                specialists.append(
                    Specialist(self.initial_time, d.type, d.quantity, d.duration)
                )
        logger.info(f"Создано {len(specialists)} специалистов")
        return tuple(specialists)

    @staticmethod
    def get_appointments_on_day(
        appointments: List[Dict], user_id: int, dt: datetime
    ) -> List[Dict]:
        """
        Получает список занятий для указанного пользователя на заданный день.

        Args:
            appointments: Список всех занятий.
            user_id: ID пользователя.
            dt: Дата для фильтрации.

        Returns:
            List[Dict]: Список занятий на указанный день.
        """
        target_day = dt.date()
        return [
            a
            for a in appointments
            if a.get("user_id") == user_id
            and datetime.fromisoformat(a["ufCrm3StartDate"]).date() == target_day
        ]

    @staticmethod
    def get_specialist_appointments_on_day(
        appointments: List[Dict], dt: datetime
    ) -> List[Dict]:
        """
        Получает список всех занятий специалиста на заданный день.

        Args:
            appointments: Список всех занятий.
            dt: Дата для фильтрации.

        Returns:
            List[Dict]: Список занятий специалиста на указанный день.
        """
        target_day = dt.date()
        return [
            a
            for a in appointments
            if datetime.fromisoformat(a["ufCrm3StartDate"]).date() == target_day
        ]

    def is_slot_ok(
        self,
        new_start: datetime,
        new_end: datetime,
        appointments: List[Dict],
        min_break: int = 15,
    ) -> bool:
        """
        Проверяет, подходит ли временной слот для нового занятия с учетом перерывов.

        Args:
            new_start: Начало нового занятия.
            new_end: Конец нового занятия.
            appointments: Список существующих и запланированных занятий.
            min_break: Минимальный перерыв между занятиями в минутах.

        Returns:
            bool: True, если слот подходит, иначе False.
        """
        logger.debug(f"Проверка слота {new_start} — {new_end} с min_break={min_break}")
        for a in appointments:
            exist_start = datetime.fromisoformat(a["ufCrm3StartDate"])
            exist_end = datetime.fromisoformat(a["ufCrm3EndDate"])
            # Проверка на пересечение
            if not (new_end <= exist_start or new_start >= exist_end):
                logger.debug(f"Обнаружено пересечение с {exist_start} — {exist_end}")
                return False
            # Проверка на минимальный перерыв
            gap_before = (new_start - exist_end).total_seconds() / 60
            gap_after = (exist_start - new_end).total_seconds() / 60
            if 0 <= gap_before < min_break:
                logger.debug(f"Слишком маленький перерыв до: {gap_before} минут")
                return False
            if 0 <= gap_after < min_break:
                logger.debug(f"Слишком маленький перерыв после: {gap_after} минут")
                return False
        logger.debug("Слот подходит")
        return True

    async def assign_appointment(
        self, chosen: Specialist, user_id: int, appoint, type_code: str, duration: int
    ) -> Dict:
        """
        Планирует занятие для выбранного специалиста, не создавая его в Bitrix.

        Args:
            chosen: Объект Specialist.
            user_id: ID пользователя.
            appoint: Объект AppointmentSchema.
            type_code: Код типа специалиста.
            duration: Продолжительность занятия в минутах.

        Returns:
            Dict: Поля для создания занятия, если слот найден, иначе None.
        """
        logger.info(
            f"Планирование занятия: type={type_code}, duration={duration}, user_id={user_id}"
        )
        for spec_id, slot in chosen.get_all_free_slots():
            if slot.duration().total_seconds() < duration * 60:
                logger.debug(f"Слот {slot.start} — {slot.end} слишком короткий")
                continue

            data = chosen.specialists_data[spec_id]
            appointments = data.setdefault("appointments", [])

            new_start = slot.start
            new_end = new_start + timedelta(minutes=duration)

            # Проверка: не более 2 занятий у ребенка в день
            child_appointments_today = self.get_appointments_on_day(
                appointments, user_id, new_start
            )
            if len(child_appointments_today) >= 2:
                logger.debug(f"У ребенка уже 2 занятия в день {new_start.date()}")
                continue

            # Проверка: не более 6 занятий у специалиста в день
            spec_appointments_today = self.get_specialist_appointments_on_day(
                appointments, new_start
            )
            if len(spec_appointments_today) >= 6:
                logger.debug(
                    f"У специалиста {spec_id} уже 6 занятий в день {new_start.date()}"
                )
                continue

            # Проверка на пересечения и перерывы
            if not self.is_slot_ok(
                new_start, new_end, appointments, min_break=self.min_break
            ):
                logger.debug(
                    f"Слот {new_start} — {new_end} не подходит из-за конфликтов или перерывов"
                )
                continue

            # Формируем поля для создания занятия
            fields = {
                "assignedById": int(spec_id),
                "ufCrm3StartDate": new_start.isoformat(),
                "ufCrm3EndDate": new_end.isoformat(),
                "ufCrm3ParentDeal": self.data.deal_id,
                "ufCrm3Child": user_id,
                "user_id": user_id,
                "ufCrm3Type": appoint.t if hasattr(appoint, "t") else type_code,
                "ufCrm3Code": type_code,
            }

            # Добавляем запланированное занятие для проверки конфликтов
            appointments.append(
                {
                    "ufCrm3StartDate": new_start.isoformat(),
                    "ufCrm3EndDate": new_end.isoformat(),
                    "user_id": user_id,
                }
            )
            chosen.specialists_data[spec_id]["appointments"] = appointments
            logger.info(
                f"Запланировано занятие для специалиста {spec_id} на {new_start} — {new_end}"
            )
            return fields

        logger.warning(
            f"Не удалось найти подходящий слот для type={type_code}, user_id={user_id}"
        )
        return None

    async def run(self) -> Dict:
        """
        Основной метод для распределения и создания занятий.

        Returns:
            Dict: Результат выполнения (список созданных занятий или сообщение об ошибке).
        """
        logger.info("Запуск распределения занятий")
        await self.update_specialists_info()
        await self.update_specialists_schedules()

        user_id = self.data.user_id
        appointments_to_create = []

        for stage_name, stage in self.data.data.items():
            logger.info(f"Обработка этапа: {stage_name}")
            for appoint in stage.data:
                type_code = appoint.type
                quantity = appoint.quantity
                duration = appoint.duration
                logger.info(
                    f"Планирование {quantity} занятий типа {type_code} длительностью {duration} минут"
                )

                candidates = [
                    spec for spec in self.specialists if spec.code == type_code
                ]
                if not candidates:
                    logger.warning(f"Не найдено специалистов для типа {type_code}")
                    continue

                for _ in range(quantity):
                    chosen = max(
                        candidates, key=lambda s: s.get_free_slots_count(), default=None
                    )
                    if not chosen or chosen.get_free_slots_count() == 0:
                        logger.warning(f"Нет доступных слотов для типа {type_code}")
                        continue

                    fields = await self.assign_appointment(
                        chosen, user_id, appoint, type_code, duration
                    )
                    if fields:
                        appointments_to_create.append(fields)
                    else:
                        logger.warning(
                            f"Не удалось запланировать занятие для типа {type_code}"
                        )

        # Проверяем, все ли занятия запланированы
        if len(appointments_to_create) == self.total_required:
            logger.info(
                f"Все {self.total_required} занятий успешно запланированы, создание в Bitrix"
            )
            cmd = {}
            for i, fields in enumerate(appointments_to_create):
                code = fields.get("ufCrm3Code", "")
                code_id = constants.listFieldValues.appointment.idByCode.get(
                    code, str(code)
                )
                batch_fields = {
                    "ASSIGNED_BY_ID": str(fields["assignedById"]),
                    "ufCrm3StartDate": str(fields["ufCrm3StartDate"]),
                    "ufCrm3EndDate": str(fields["ufCrm3EndDate"]),
                    "ufCrm3ParentDeal": str(fields["ufCrm3ParentDeal"]),
                    "ufCrm3Child": str(fields["ufCrm3Child"]),
                    "ufCrm3Type": str(fields["ufCrm3Type"]),
                    "ufCrm3Code": str(code_id),
                    "ufCrm3Status": "50",  # Статус "Забронировано"
                }
                cmd[i] = BatchBuilder(
                    "crm.item.add",
                    {
                        "entityTypeId": constants.entityTypeId.appointment,
                        "fields": batch_fields,
                    },
                ).build()

            response = await bitrix.call_batch(cmd)
            all_succeeded = all(
                isinstance(response.get(str(i), {}).get("result", {}), dict)
                and "id" in response[str(i)]["result"]
                for i in cmd
            )

            if all_succeeded:
                logger.info("Все занятия успешно созданы в Bitrix")
                return {"appointments": appointments_to_create}
            else:
                logger.error("Не все занятия созданы, выполняется откат")
                created = [
                    i
                    for i in cmd
                    if isinstance(response.get(str(i), {}).get("result", {}), dict)
                    and "id" in response[str(i)]["result"]
                ]
                for i in created:
                    item_id = response[str(i)]["result"]["id"]
                    await bitrix.call(
                        "crm.item.delete",
                        {
                            "id": item_id,
                            "entityTypeId": constants.entityTypeId.appointment,
                        },
                    )
                    logger.info(f"Удалено занятие с ID {item_id}")
                return {"error": "Не все занятия удалось создать, выполнен откат"}
        else:
            logger.error(
                f"Запланировано {len(appointments_to_create)} из {self.total_required} занятий"
            )
            return {"error": "Не все занятия удалось запланировать"}

    async def update_specialists_info(self):
        """Обновляет информацию о доступных специалистах."""
        departments = await bitrix.get_all_departments()
        batches = tuple(
            s.get_specialists_info_batch(departments) for s in self.specialists
        )
        cmd = {index: value for index, value in enumerate(batches)}
        response = await bitrix.call_batch(cmd)
        for index, specs in enumerate(self.specialists):
            specs.possible_specs = response[index]
        logger.info("Информация о специалистах обновлена")

    async def update_specialists_schedules(self):
        """Получает графики и расписания занятий для всех специалистов."""
        cmd = {}
        date_start = self.initial_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_start_iso = date_start.isoformat()
        batch_index = 0
        mapping = {}

        for spec in self.specialists:
            for possible_spec in spec.possible_specs:
                specialist_id = possible_spec.get("ID")
                if not specialist_id:
                    continue

                cmd[batch_index] = BatchBuilder(
                    "crm.item.list",
                    {
                        "entityTypeId": 1042,
                        "filter": {
                            ">=ufCrm4Date": date_start_iso,
                            "assignedById": specialist_id,
                        },
                        "order": {"ufCrm4Date": "ASC"},
                    },
                ).build()
                mapping[batch_index] = (spec, specialist_id, "schedule")
                batch_index += 1

                cmd[batch_index] = BatchBuilder(
                    "crm.item.list",
                    {
                        "entityTypeId": 1036,
                        "filter": {
                            ">=ufCrm3StartDate": date_start_iso,
                            "assignedById": specialist_id,
                        },
                        "order": {"ufCrm3StartDate": "ASC"},
                    },
                ).build()
                mapping[batch_index] = (spec, specialist_id, "appointments")
                batch_index += 1

        response = await bitrix.call_batch(cmd)
        for idx, (spec, specialist_id, typ) in mapping.items():
            items = (
                response[idx]
                .get("result", {})
                .get("items", response[idx].get("items", []))
            )
            if not hasattr(spec, "specialists_data"):
                spec.specialists_data = {}
            if specialist_id not in spec.specialists_data:
                spec.specialists_data[specialist_id] = {
                    "schedule": [],
                    "appointments": [],
                }
            spec.specialists_data[specialist_id][typ] = items
        logger.info("Графики и расписания специалистов обновлены")

    async def create_schedule_entry(self, fields: Dict, specialist=None) -> Dict:
        """
        Создает запись занятия в Bitrix (используется для тестирования или других целей).

        Args:
            fields: Поля для создания записи.
            specialist: Объект Specialist (опционально).

        Returns:
            Dict: Ответ от Bitrix.
        """
        entityTypeId = constants.entityTypeId.appointment
        code = fields.get("ufCrm3Code") or (
            specialist.code if specialist and hasattr(specialist, "code") else None
        )
        code_id = constants.listFieldValues.appointment.idByCode.get(code, str(code))
        status_id = 50  # Статус "Забронировано"

        response = await bitrix.call(
            "crm.item.add",
            {
                "entityTypeId": entityTypeId,
                "fields": {
                    "ASSIGNED_BY_ID": str(fields.get("assignedById")),
                    "ufCrm3StartDate": str(fields.get("ufCrm3StartDate")),
                    "ufCrm3EndDate": str(fields.get("ufCrm3EndDate")),
                    "ufCrm3ParentDeal": str(fields.get("ufCrm3ParentDeal")),
                    "ufCrm3Child": str(fields.get("ufCrm3Child")),
                    "user_id": str(fields.get("user_id")),
                    "ufCrm3Type": str(fields.get("ufCrm3Type")),
                    "ufCrm3Status": str(status_id),
                    "ufCrm3Code": str(code_id),
                },
            },
        )
        logger.info(f"Создано занятие в Bitrix: {response}")
        return response
