from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
from app.settings import Settings
from app.schemas import RequestSchemaV2
from app import bitrix
from app.utils import BatchBuilder
from api.constants import constants
from .specialist import Specialist

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HandlerV2:
    """Обработчик для распределения занятий на основе данных запроса версии 2.

    Attributes:
        initial_time (datetime): Начальная дата для планирования (текущая дата + 1 день).
        data (RequestSchemaV2): Данные запроса.
        specialists (Tuple[Specialist]): Кортеж специалистов для назначений.
        total_required (int): Общее количество необходимых занятий.
        min_break (int): Минимальный перерыв между занятиями (в минутах).
        max_break (int): Максимальный перерыв между занятиями (в минутах).
        total_duration (int): Общая длительность периода планирования (в днях).
    """

    def __init__(self, data: RequestSchemaV2):
        """Инициализирует обработчик с данными запроса.

        Args:
            data (RequestSchemaV2): Данные запроса для обработки.

        """
        self.initial_time = datetime.now(Settings.TIMEZONE) + timedelta(days=1)
        self.data = data
        self.specialists = self._create_specialists()
        self.total_required = sum(
            appoint.quantity
            for stage in self.data.data.values()
            for appoint in stage.data
        )
        self.min_break = 1
        self.max_break = 45
        self.total_duration = sum(
            stage.duration * 7 for stage in self.data.data.values()
        )
        logger.info(
            f"Инициализирован Handler: deal_id={self.data.deal_id}, user_id={self.data.user_id}, "
            f"всего занятий={self.total_required}, период={self.total_duration} дней"
        )

    def _create_specialists(self) -> Tuple[Specialist]:
        """Создает специалистов для каждого назначения в каждом этапе.

        Returns:
            Tuple[Specialist]: Кортеж объектов Specialist для всех назначений.
        """
        specialists = []
        for stage_name, stage in self.data.data.items():
            for appoint in stage.data:
                specialists.append(
                    Specialist(
                        self.initial_time,
                        appoint.type,
                        appoint.quantity,
                        appoint.duration,
                        stage.duration,
                    )
                )
        logger.info(f"Создано {len(specialists)} специалистов")
        return tuple(specialists)

    def _get_child_appointments_on_day(self, user_id: int, dt: datetime) -> List[Dict]:
        """Получает все занятия ребенка за указанный день.

        Args:
            user_id (int): ID ребенка.
            dt (datetime): Дата для проверки.

        Returns:
            List[Dict]: Список словарей с данными о занятиях за указанный день.
        """
        target_day = dt.date()
        all_appointments = []
        for spec in self.specialists:
            for spec_id, data in spec.specialists_data.items():
                appointments = data.get("appointments", [])
                all_appointments.extend(
                    a
                    for a in appointments
                    if a.get("user_id") == user_id
                    and datetime.fromisoformat(a["ufCrm3StartDate"]).date()
                    == target_day
                )
        logger.debug(f"Найдено {len(all_appointments)} занятий ребенка на {target_day}")
        return all_appointments

    def _get_specialist_appointments_on_day(
        self, appointments: List[Dict], dt: datetime
    ) -> List[Dict]:
        """Получает все занятия специалиста за указанный день.

        Args:
            appointments (List[Dict]): Список всех занятий специалиста.
            dt (datetime): Дата для проверки.

        Returns:
            List[Dict]: Список занятий специалиста за указанный день.
        """
        target_day = dt.date()
        return [
            a
            for a in appointments
            if datetime.fromisoformat(a["ufCrm3StartDate"]).date() == target_day
        ]

    def _is_slot_ok(
        self, new_start: datetime, new_end: datetime, appointments: List[Dict]
    ) -> bool:
        """Проверяет, подходит ли временной слот для специалиста.

        Args:
            new_start (datetime): Начало нового занятия.
            new_end (datetime): Окончание нового занятия.
            appointments (List[Dict]): Список существующих занятий.

        Returns:
            bool: True, если слот свободен и соответствует требованиям, иначе False.
        """
        for a in appointments:
            exist_start = datetime.fromisoformat(a["ufCrm3StartDate"])
            exist_end = datetime.fromisoformat(a["ufCrm3EndDate"])
            if not (new_end <= exist_start or new_start >= exist_end):
                logger.debug(f"Пересечение с {exist_start} — {exist_end}")
                return False
            if exist_end <= new_start < exist_end + timedelta(minutes=self.min_break):
                logger.debug(f"Слишком малый перерыв перед {new_start}")
                return False
            if exist_start > new_end and exist_start - new_end < timedelta(
                minutes=self.min_break
            ):
                logger.debug(f"Слишком малый перерыв после {new_end}")
                return False
        return True

    def _check_child_schedule(
        self, child_appointments: List[Dict], new_start: datetime, new_end: datetime
    ) -> bool:
        """Проверяет расписание ребенка на возможность добавления занятия.

        Args:
            child_appointments (List[Dict]): Список текущих занятий ребенка за день.
            new_start (datetime): Начало нового занятия.
            new_end (datetime): Окончание нового занятия.

        Returns:
            bool: True, если можно добавить занятие, иначе False.
        """
        # Проверяем пересечения с существующими занятиями
        for existing in child_appointments:
            exist_start = datetime.fromisoformat(existing["ufCrm3StartDate"])
            exist_end = datetime.fromisoformat(existing["ufCrm3EndDate"])
            if not (new_end <= exist_start or new_start >= exist_end):
                logger.debug(f"Пересечение с {exist_start} — {exist_end}")
                return False
        return True

    async def _fetch_alternative_specialists(
        self, type_code: str, chosen: Specialist
    ) -> List[Dict]:
        """Получает список альтернативных специалистов для указанного типа занятия.

        Args:
            type_code (str): Код типа занятия.
            chosen (Specialist): Объект специалиста.

        Returns:
            List[Dict]: Список данных об альтернативных специалистах.
        """
        departments = await bitrix.get_all_departments()
        department_ids = [
            id for id, dept in departments.items() if type_code in dept.get("NAME", "")
        ]
        cmd = {
            f"dept_{dept_id}": BatchBuilder(
                "user.get",
                {
                    "filter": {"ACTIVE": True, "%UF_DEPARTMENT": dept_id},
                    "order": {"ID": "ASC"},
                },
            ).build()
            for dept_id in department_ids
        }
        try:
            response = await bitrix.call_batch(cmd)
            specs = []
            for dept_id in department_ids:
                key = f"dept_{dept_id}"
                if key in response and isinstance(response[key], list):
                    specs.extend(response[key])
            return specs
        except Exception as e:
            logger.error(f"Ошибка получения специалистов для отдела: {e}")
            return []

    async def _update_alternative_specialist_data(
        self, spec: Dict, chosen: Specialist, date_start: datetime, date_end: datetime
    ) -> None:
        """Обновляет данные об альтернативном специалисте.

        Args:
            spec (Dict): Данные специалиста.
            chosen (Specialist): Объект специалиста.
            date_start (datetime): Начало периода.
            date_end (datetime): Окончание периода.
        """
        spec_id = spec.get("ID")
        if not spec_id or spec_id in chosen.specialists_data:
            return
        chosen.specialists_data[spec_id] = {"schedule": [], "appointments": []}
        date_start_iso = date_start.isoformat()
        date_end_iso = date_end.isoformat()
        cmd = {
            f"schedule_{spec_id}": BatchBuilder(
                "crm.item.list",
                {
                    "entityTypeId": 1042,
                    "filter": {
                        ">=ufCrm4Date": date_start_iso,
                        "<ufCrm4Date": date_end_iso,
                        "assignedById": spec_id,
                    },
                },
            ).build(),
            f"appointments_{spec_id}": BatchBuilder(
                "crm.item.list",
                {
                    "entityTypeId": 1036,
                    "filter": {
                        ">=ufCrm3StartDate": date_start_iso,
                        "<ufCrm3StartDate": date_end_iso,
                        "assignedById": spec_id,
                    },
                },
            ).build(),
        }
        try:
            response = await bitrix.call_batch(cmd)
            chosen.specialists_data[spec_id]["schedule"] = response.get(
                f"schedule_{spec_id}", {}
            ).get("items", [])
            chosen.specialists_data[spec_id]["appointments"] = response.get(
                f"appointments_{spec_id}", {}
            ).get("items", [])
        except Exception as e:
            logger.error(f"Ошибка загрузки данных для {spec_id}: {e}")

    async def _try_assign_appointment(
        self,
        chosen: Specialist,
        user_id: int,
        type_code: str,
        duration: int,
        target_date: datetime,
    ) -> Optional[Dict]:
        """Пытается назначить занятие для выбранного специалиста в указанный день.

        Args:
            chosen (Specialist): Объект специалиста.
            user_id (int): ID ребенка.
            type_code (str): Код типа занятия.
            duration (int): Длительность занятия в минутах.
            target_date (datetime): Целевая дата для назначения.

        Returns:
            Optional[Dict]: Данные о назначенном занятии или None, если назначить не удалось.
        """
        free_slots = chosen.get_all_free_slots()
        logger.debug(
            f"Найдено {len(free_slots)} слотов для типа {type_code} на {target_date}"
        )

        for spec_id, slot in free_slots:
            # Проверяем, что слот находится в целевой день
            if slot.start.date() != target_date:
                continue

            slot_duration = (slot.end - slot.start).total_seconds() / 60
            if slot_duration < duration:
                continue

            new_start = slot.start
            new_end = new_start + timedelta(minutes=duration)
            appointments = chosen.specialists_data.get(spec_id, {}).get(
                "appointments", []
            )

            # Проверяем расписание ребенка
            child_appointments_today = self._get_child_appointments_on_day(
                user_id, new_start
            )
            if not self._check_child_schedule(
                child_appointments_today, new_start, new_end
            ):
                continue

            # Проверяем, не превышен ли лимит занятий специалиста в день (6)
            spec_appointments_today = self._get_specialist_appointments_on_day(
                appointments, new_start
            )
            if len(spec_appointments_today) >= 6:
                logger.debug(
                    f"Специалист {spec_id} имеет 6 занятий на {new_start.date()}"
                )
                continue

            # Проверяем, подходит ли слот (пересечения и перерывы)
            if not self._is_slot_ok(new_start, new_end, appointments):
                continue

            children_id = await self._get_children_id(self.data.deal_id)
            fields = {
                "assignedById": int(spec_id),
                "ufCrm3StartDate": new_start.isoformat(),
                "ufCrm3EndDate": new_end.isoformat(),
                "ufCrm3ParentDeal": self.data.deal_id,
                "ufCrm3Children": children_id if children_id else 158,
                "user_id": user_id,
                "ufCrm3Type": type_code,
                "ufCrm3Code": type_code,
            }
            new_appt = {
                "ufCrm3StartDate": new_start.isoformat(),
                "ufCrm3EndDate": new_end.isoformat(),
                "user_id": user_id,
                "ufCrm3Type": type_code,
            }
            appointments.append(new_appt)
            chosen.specialists_data[spec_id]["appointments"] = appointments
            logger.info(f"Назначено занятие для {spec_id} на {new_start} — {new_end}")
            return fields
        return None

    async def assign_appointment(
        self, chosen: Specialist, user_id: int, type_code: str, duration: int
    ) -> Optional[Dict]:
        """Назначает занятие, проверяя слоты у выбранного специалиста или альтернативных.

        Args:
            chosen (Specialist): Объект специалиста.
            user_id (int): ID ребенка.
            type_code (str): Код типа занятия.
            duration (int): Длительность занятия в минутах.

        Returns:
            Optional[Dict]: Данные о назначенном занятии или None, если назначить не удалось.
        """
        logger.info(
            f"Назначение занятия: type={type_code}, duration={duration}, user_id={user_id}"
        )

        # Пробуем назначить с основным специалистом
        fields = await self._try_assign_appointment(
            chosen, user_id, type_code, duration
        )
        if fields:
            return fields

        # Если не удалось, ищем альтернативных специалистов
        logger.warning(
            f"Не найдено слотов у основного специалиста для {type_code}, ищем альтернативных"
        )
        date_start = self.initial_time.replace(hour=0, minute=0)
        date_end = date_start + timedelta(days=self.total_duration)
        specs = await self._fetch_alternative_specialists(type_code, chosen)

        for spec in specs:
            await self._update_alternative_specialist_data(
                spec, chosen, date_start, date_end
            )
            fields = await self._try_assign_appointment(
                chosen, user_id, type_code, duration
            )
            if fields:
                return fields

        logger.error(f"Не удалось назначить занятие для {type_code}")
        return None

    async def _create_appointments_batch(
        self, appointments_to_create: List[Dict]
    ) -> Tuple[List[str], List[Dict]]:
        """Создает пакет для добавления занятий в Bitrix.

        Args:
            appointments_to_create (List[Dict]): Список данных о занятиях для создания.

        Returns:
            Tuple[List[str], List[Dict]]: Список ID созданных занятий и сами данные.
        """
        cmd = {}
        children_id = await self._get_children_id(self.data.deal_id)
        for i, fields in enumerate(appointments_to_create):
            code_id = constants.listFieldValues.appointment.idByCode.get(
                fields["ufCrm3Code"], fields["ufCrm3Code"]
            )
            cmd[f"create_{i}"] = BatchBuilder(
                "crm.item.add",
                {
                    "entityTypeId": constants.entityTypeId.appointment,
                    "fields": {
                        "ASSIGNED_BY_ID": str(fields["assignedById"]),
                        "ufCrm3StartDate": fields["ufCrm3StartDate"],
                        "ufCrm3EndDate": fields["ufCrm3EndDate"],
                        "ufCrm3ParentDeal": str(fields["ufCrm3ParentDeal"]),
                        "ufCrm3Children": children_id if children_id else 158,
                        "ufCrm3Type": fields["ufCrm3Type"],
                        "ufCrm3Code": str(code_id),
                        "ufCrm3Status": "50",
                    },
                },
            ).build()

        created_ids = []
        try:
            response = await bitrix.call_batch(cmd)
            for i, fields in enumerate(appointments_to_create):
                item = response.get(f"create_{i}", {}).get("item", {})
                if item.get("id"):
                    fields["id"] = item["id"]
                    created_ids.append(item["id"])
                else:
                    raise Exception(
                        f"Не удалось создать занятие {i}: {response.get(f'create_{i}')}"
                    )
            logger.info("Все занятия успешно созданы")
            return created_ids, appointments_to_create
        except Exception as e:
            logger.error(f"Ошибка создания занятий: {e}")
            return created_ids, []

    async def _delete_failed_appointments(self, created_ids: List[str]) -> None:
        """Удаляет созданные занятия в случае ошибки.

        Args:
            created_ids (List[str]): Список ID созданных занятий для удаления.
        """
        cmd = {
            f"delete_appointment_{appointment_id}": {
                "method": "crm.item.delete",
                "params": {
                    "id": appointment_id,
                    "entityTypeId": constants.entityTypeId.appointment,
                },
            }
            for appointment_id in created_ids
        }
        await bitrix.call_batch(cmd)

    async def run(self) -> Dict:
        """Запускает процесс распределения занятий.

        Returns:
            Dict: Результат выполнения с данными о созданных занятиях или ошибкой.
        """
        logger.info("Запуск распределения занятий")
        await self.update_specialists_info()
        await self._update_specialists_schedules()

        user_id = self.data.user_id
        appointments_to_create = []
        failed_appointments = []

        # Собираем все назначения по типам
        appointments_by_type = []
        for stage_name, stage in self.data.data.items():
            logger.info(f"Обработка этапа: {stage_name}")
            for appoint in stage.data:
                for _ in range(appoint.quantity):
                    appointments_by_type.append(
                        {
                            "type_code": appoint.type,
                            "duration": appoint.duration,
                            "candidates": [
                                spec
                                for spec in self.specialists
                                if spec.code == appoint.type
                            ],
                        }
                    )

        # Планируем занятия по дням, стараясь заполнить максимально
        current_day = self.initial_time.date()
        end_date = current_day + timedelta(days=self.total_duration)
        remaining_appointments = appointments_by_type.copy()

        while remaining_appointments and current_day <= end_date:
            logger.info(f"Планирование занятий на {current_day}")
            # Перемешиваем назначения для равномерного распределения типов
            import random

            random.shuffle(remaining_appointments)

            for appt in remaining_appointments[:]:  # Копируем список для удаления
                type_code = appt["type_code"]
                duration = appt["duration"]
                candidates = appt["candidates"]

                if not candidates:
                    logger.error(f"Нет специалистов для типа {type_code}")
                    failed_appointments.append(
                        {"type": type_code, "duration": duration}
                    )
                    remaining_appointments.remove(appt)
                    continue

                for candidate in candidates:
                    fields = await self._try_assign_appointment(
                        candidate, user_id, type_code, duration, current_day
                    )
                    if fields:
                        appointments_to_create.append(fields)
                        remaining_appointments.remove(appt)
                        logger.info(
                            f"Назначено занятие типа {type_code} на {current_day}"
                        )
                        break
                else:
                    logger.debug(
                        f"Не удалось назначить занятие типа {type_code} на {current_day}"
                    )

            # Переходим к следующему дню
            current_day += timedelta(days=1)

        if remaining_appointments:
            error_msg = "Не удалось запланировать занятия:\n" + "\n".join(
                f"- Тип: {appt['type_code']}, Длительность: {appt['duration']} мин"
                for appt in remaining_appointments
            )
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info(f"Создание {len(appointments_to_create)} занятий в Bitrix")
        created_ids, appointments_to_create = await self._create_appointments_batch(
            appointments_to_create
        )
        if not created_ids:
            await self._delete_failed_appointments(created_ids)
            return {"error": "Ошибка создания занятий"}
        return {"appointments": appointments_to_create}

    async def update_specialists_info(self) -> None:
        """Обновляет информацию о специалистах."""
        logger.info("Обновление информации о специалистах")
        departments = await bitrix.get_all_departments()
        cmd = {
            f"spec_{i}": s.get_specialists_info_batch(departments)
            for i, s in enumerate(self.specialists)
        }
        try:
            response = await bitrix.call_batch(cmd)
            for i, spec in enumerate(self.specialists):
                specs_list = response.get(f"spec_{i}", [])
                spec.possible_specs = specs_list if isinstance(specs_list, list) else []
                spec.specialists_data = {
                    str(s["ID"]): {"schedule": [], "appointments": []}
                    for s in spec.possible_specs
                    if "ID" in s
                }
                if not spec.possible_specs:
                    logger.warning(f"Нет специалистов для {spec.code}")
        except Exception as e:
            logger.error(f"Ошибка получения информации о специалистах: {e}")
            for spec in self.specialists:
                spec.possible_specs = []
                spec.specialists_data = {}

    async def _get_children_id(self, deal_id: int) -> Optional[int]:
        """Получает ID ребенка из данных сделки.

        Args:
            deal_id (int): ID сделки.

        Returns:
            Optional[int]: ID ребенка или None, если не удалось получить.
        """
        cmd = {
            "deal_info": BatchBuilder(
                "crm.deal.list", {"filter": {"ID": deal_id}, "select": ["*"]}
            ).build()
        }
        try:
            response = await bitrix.call_batch(cmd=cmd)
            if response.get("deal_info"):
                contact_id = response["deal_info"][0]["CONTACT_ID"]
                if contact_id:
                    return int(contact_id)
        except Exception as e:
            logger.error(f"Ошибка получения данных сделки: {e}")
        return None

    async def _update_specialists_schedules(self) -> None:
        """Обновляет графики специалистов на весь период."""
        logger.info("Обновление графиков специалистов")
        cmd = {}
        date_start = self.initial_time.replace(hour=0, minute=0)
        date_end = date_start + timedelta(days=self.total_duration)
        date_start_iso = date_start.isoformat()
        date_end_iso = date_end.isoformat()
        mapping = {}

        for spec in self.specialists:
            if not spec.possible_specs:
                continue
            for ps in spec.possible_specs:
                spec_id = ps.get("ID")
                if not spec_id:
                    continue
                if spec_id not in spec.specialists_data:
                    spec.specialists_data[spec_id] = {
                        "schedule": [],
                        "appointments": [],
                    }
                idx = len(cmd)
                cmd[f"schedule_{idx}"] = BatchBuilder(
                    "crm.item.list",
                    {
                        "entityTypeId": 1042,
                        "filter": {
                            ">=ufCrm4Date": date_start_iso,
                            "<ufCrm4Date": date_end_iso,
                            "assignedById": spec_id,
                        },
                    },
                ).build()
                mapping[f"schedule_{idx}"] = (spec, spec_id, "schedule")
                cmd[f"appointments_{idx}"] = BatchBuilder(
                    "crm.item.list",
                    {
                        "entityTypeId": 1036,
                        "filter": {
                            ">=ufCrm3StartDate": date_start_iso,
                            "<ufCrm3StartDate": date_end_iso,
                            "assignedById": spec_id,
                        },
                    },
                ).build()
                mapping[f"appointments_{idx}"] = (spec, spec_id, "appointments")

        if not cmd:
            logger.error("Нет данных для загрузки графиков")
            return

        try:
            response = await bitrix.call_batch(cmd)
            for key, (spec, spec_id, typ) in mapping.items():
                result = response.get(key, {})
                items = result.get("items", [])
                spec.specialists_data[spec_id][typ] = (
                    items if isinstance(items, list) else []
                )
                if not items and typ == "schedule":
                    logger.warning(f"Нет графика для специалиста {spec_id}")
        except Exception as e:
            logger.error(f"Ошибка загрузки графиков: {e}")
            for spec in self.specialists:
                for spec_id in spec.specialists_data:
                    spec.specialists_data[spec_id] = {
                        "schedule": [],
                        "appointments": [],
                    }
