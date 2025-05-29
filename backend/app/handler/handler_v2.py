from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
from app.settings import Settings
from app.schemas import RequestSchemaV2
from app import bitrix
from app.utils import BatchBuilder
from api.constants import constants
from .specialist import Specialist

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HandlerV2:
    def __init__(self, data: RequestSchemaV2):
        self.initial_time = datetime.now(Settings.TIMEZONE) + timedelta(days=1)
        self.data = data
        self.specialists = self.create_specialists()
        self.total_required = sum(
            appoint.quantity
            for stage in self.data.data.values()
            for appoint in stage.data
        )
        self.min_break = 15  # Минимальный перерыв между занятиями в минутах
        self.max_break = 45  # Максимальный перерыв между занятиями пользователя в день
        logger.info(
            f"Инициализирован Handler для deal_id={self.data.deal_id}, user_id={self.data.user_id}, "
            f"всего занятий={self.total_required}"
        )

    def create_specialists(self) -> Tuple[Specialist]:
        specialists = []
        for stage in self.data.data.values():
            for d in stage.data:
                specialists.append(
                    Specialist(self.initial_time, d.type, d.quantity, d.duration)
                )
        logger.info(f"Создано {len(specialists)} специалистов")
        return tuple(specialists)

    def get_appointments_on_day(
        self, appointments: List[Dict], user_id: int, dt: datetime
    ) -> List[Dict]:
        target_day = dt.date()
        return [
            a
            for a in appointments
            if a.get("user_id") == user_id
            and datetime.fromisoformat(a["ufCrm3StartDate"]).date() == target_day
        ]

    def get_specialist_appointments_on_day(
        self, appointments: List[Dict], dt: datetime
    ) -> List[Dict]:
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
        logger.debug(f"Проверка слота {new_start} — {new_end} с min_break={min_break}")
        if not appointments:
            logger.debug("Слот свободен (нет других занятий)")
            return True

        for a in appointments:
            exist_start = datetime.fromisoformat(a["ufCrm3StartDate"])
            exist_end = datetime.fromisoformat(a["ufCrm3EndDate"])
            if not (new_end <= exist_start or new_start >= exist_end):
                logger.debug(f"Обнаружено пересечение с {exist_start} — {exist_end}")
                return False
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
        logger.info(
            f"Планирование занятия: type={type_code}, duration={duration}, user_id={user_id}"
        )
        free_slots = chosen.get_all_free_slots()
        logger.debug(
            f"Найдено {len(free_slots)} свободных слотов для специалиста типа {type_code}"
        )

        if not free_slots:
            logger.warning(f"Нет свободных слотов для типа {type_code}")
            return None

        for spec_id, slot in free_slots:
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            if slot_duration < duration:
                logger.debug(
                    f"Слот {slot.start} — {slot.end} слишком короткий ({slot_duration} мин < {duration} мин)"
                )
                continue

            data = chosen.specialists_data.get(spec_id, {})
            appointments = data.get("appointments", [])

            new_start = slot.start
            new_end = new_start + timedelta(minutes=duration)

            logger.debug(
                f"Проверяем слот {new_start} — {new_end} для специалиста {spec_id}"
            )

            # Проверка: не более 2 занятий у ребенка в день
            child_appointments_today = self.get_appointments_on_day(
                appointments, user_id, new_start
            )
            if len(child_appointments_today) >= 2:
                logger.debug(
                    f"Отклонено: уже 2 занятия у ребенка в день {new_start.date()}"
                )
                continue

            # Проверка: не более 6 занятий у специалиста в день
            spec_appointments_today = self.get_specialist_appointments_on_day(
                appointments, new_start
            )
            if len(spec_appointments_today) >= 6:
                logger.debug(
                    f"Отклонено: уже 6 занятий у специалиста {spec_id} в день {new_start.date()}"
                )
                continue

            # Проверка: слот не конфликтует с существующими занятиями
            if not self.is_slot_ok(
                new_start, new_end, appointments, min_break=self.min_break
            ):
                logger.debug(f"Отклонено: не подходит из-за минимального перерыва")
                continue

            # Проверка на максимальный перерыв для пользователя
            user_appointments_same_day = [
                a
                for a in appointments
                if a["user_id"] == user_id
                and datetime.fromisoformat(a["ufCrm3StartDate"]).date()
                == new_start.date()
            ]
            new_appt = {
                "ufCrm3StartDate": new_start.isoformat(),
                "ufCrm3EndDate": new_end.isoformat(),
                "user_id": user_id,
                "ufCrm3Type": type_code,
            }
            all_user_same_day = user_appointments_same_day + [new_appt]
            sorted_all = sorted(
                all_user_same_day,
                key=lambda x: datetime.fromisoformat(x["ufCrm3StartDate"]),
            )
            ok = True
            for i in range(1, len(sorted_all)):
                prev_end = datetime.fromisoformat(sorted_all[i - 1]["ufCrm3EndDate"])
                curr_start = datetime.fromisoformat(sorted_all[i]["ufCrm3StartDate"])
                gap = (curr_start - prev_end).total_seconds() / 60
                if gap > self.max_break:
                    ok = False
                    logger.debug(
                        f"Слот {new_start} — {new_end} создает слишком большой перерыв > {self.max_break} мин "
                        f"для пользователя {user_id} на {new_start.date()}"
                    )
                    break
            if not ok:
                continue

            # Проверка: максимум 2 занятия типа R в день
            if type_code == "R":
                r_appointments_today = [
                    a for a in child_appointments_today if a.get("ufCrm3Type") == "R"
                ]
                if len(r_appointments_today) >= 2:
                    logger.debug(
                        f"У ребенка уже 2 занятия типа R в день {new_start.date()}"
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

            # Добавляем запланированное занятие
            appointments.append(new_appt)
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
        logger.info("Запуск распределения занятий")
        await self.update_specialists_info()
        await self.update_specialists_schedules()

        user_id = self.data.user_id
        appointments_to_create = []
        max_days = 30  # Ограничение на количество дней
        current_day = 0

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
                    if current_day >= max_days:
                        logger.error(
                            f"Превышен лимит дней ({max_days}) для планирования"
                        )
                        return {
                            "error": f"Не удалось запланировать все занятия за {max_days} дней"
                        }

                    for candidate in candidates:
                        fields = await self.assign_appointment(
                            candidate, user_id, appoint, type_code, duration
                        )
                        if fields:
                            appointments_to_create.append(fields)
                            break
                    else:
                        logger.warning(
                            f"Не удалось найти слот для типа {type_code} на день {self.initial_time.date()}"
                        )
                        self.initial_time += timedelta(days=1)
                        current_day += 1
                        await self.update_specialists_schedules()
                        continue

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
                    "ufCrm3Status": "50",
                }
                cmd[i] = BatchBuilder(
                    "crm.item.add",
                    {
                        "entityTypeId": constants.entityTypeId.appointment,
                        "fields": batch_fields,
                    },
                ).build()

            response = await bitrix.call_batch(cmd)
            logger.info(f"response: {response}")
            # Проверяем ответ как список словарей
            all_succeeded = all(
                isinstance(item, dict) and "item" in item and "id" in item["item"]
                for item in response
            )

            if all_succeeded:
                logger.info("Все занятия успешно созданы в Bitrix")
                return {"appointments": appointments_to_create}
            else:
                logger.error("Не все занятия созданы, выполняется откат")
                created = [
                    i
                    for i, item in enumerate(response)
                    if isinstance(item, dict)
                    and "item" in item
                    and "id" in item["item"]
                ]
                for i in created:
                    item_id = response[i]["item"]["id"]
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
        departments = await bitrix.get_all_departments()
        batches = tuple(
            s.get_specialists_info_batch(departments) for s in self.specialists
        )
        cmd = {index: value for index, value in enumerate(batches)}
        response = await bitrix.call_batch(cmd)
        logger.debug(f"Ответ Bitrix в update_specialists_info: {response}")

        for index, specs in enumerate(self.specialists):
            try:
                # Ответ — список списков специалистов
                specs_list = response[index] if index < len(response) else []
                if not isinstance(specs_list, list):
                    logger.error(
                        f"Некорректный формат ответа для index={index}: {specs_list}"
                    )
                    specs_list = []
                specs.possible_specs = specs_list
                logger.debug(
                    f"Загружено {len(specs.possible_specs)} специалистов для code={specs.code}"
                )
            except (IndexError, TypeError) as e:
                logger.error(f"Ошибка обработки ответа для index={index}: {e}")
                specs.possible_specs = []

        # Если possible_specs пустое, используем дефолтные ID специалистов
        for specs in self.specialists:
            if not specs.possible_specs:
                logger.warning(
                    f"Нет специалистов для code={specs.code}, задаю дефолтные"
                )
                default_specs = {
                    "R": [{"ID": "12"}],
                    "LM": [{"ID": "19"}, {"ID": "20"}, {"ID": "21"}, {"ID": "22"}],
                }.get(specs.code, [])
                specs.possible_specs = default_specs
                logger.debug(
                    f"Установлено {len(default_specs)} дефолтных специалистов для code={specs.code}"
                )

        logger.info("Информация о специалистах обновлена")

    async def update_specialists_schedules(self):
        logger.info("Обновление графиков специалистов")
        cmd = {}
        date_start = self.initial_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_end = date_start + timedelta(days=30)
        date_start_iso = date_start.isoformat()
        date_end_iso = date_end.isoformat()
        batch_index = 0
        mapping = {}

        # Инициализируем specialists_data для всех возможных специалистов
        for spec in self.specialists:
            for possible_spec in spec.possible_specs:
                specialist_id = possible_spec.get("ID")
                if specialist_id and specialist_id not in spec.specialists_data:
                    spec.specialists_data[specialist_id] = {
                        "schedule": [],
                        "appointments": [],
                    }

        # Формируем батчи для запроса графиков и занятий
        for spec in self.specialists:
            for possible_spec in spec.possible_specs:
                specialist_id = possible_spec.get("ID")
                if not specialist_id:
                    logger.warning(f"Отсутствует ID специалиста для code={spec.code}")
                    continue

                cmd[batch_index] = BatchBuilder(
                    "crm.item.list",
                    {
                        "entityTypeId": 1042,
                        "filter": {
                            ">=ufCrm4Date": date_start_iso,
                            "<ufCrm4Date": date_end_iso,
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
                            "<ufCrm3StartDate": date_end_iso,
                            "assignedById": specialist_id,
                        },
                        "order": {"ufCrm3StartDate": "ASC"},
                    },
                ).build()
                mapping[batch_index] = (spec, specialist_id, "appointments")
                batch_index += 1

        if cmd:
            response = await bitrix.call_batch(cmd)
            logger.debug(f"Ответ Bitrix в update_specialists_schedules: {response}")

            # Обрабатываем ответ как список
            for idx, (spec, specialist_id, typ) in mapping.items():
                try:
                    result = response[idx] if idx < len(response) else {}
                    items = result.get("result", {}).get("items", [])
                    if not isinstance(items, list):
                        logger.error(
                            f"Некорректный формат данных для специалиста {specialist_id}: {items}"
                        )
                        items = []
                    logger.debug(
                        f"Загружено {len(items)} {typ} для специалиста {specialist_id}"
                    )
                    spec.specialists_data[specialist_id][typ] = items
                except (IndexError, TypeError) as e:
                    logger.error(
                        f"Ошибка обработки ответа для специалиста {specialist_id}, тип {typ}: {e}"
                    )
                    spec.specialists_data[specialist_id][typ] = []
        else:
            logger.warning("Нет батчей для запроса графиков")

        # Добавление fallback-графиков
        for spec in self.specialists:
            for spec_id, data in spec.specialists_data.items():
                if not data["schedule"]:
                    logger.warning(
                        f"Нет графика для специалиста {spec_id}, создаю дефолтные"
                    )
                    data["schedule"] = []
                    current_date = date_start
                    while current_date <= date_end:
                        start_time = current_date.replace(
                            hour=9, minute=0, second=0, microsecond=0
                        )
                        end_time = current_date.replace(
                            hour=18, minute=0, second=0, microsecond=0
                        )
                        start_ms = int(start_time.timestamp() * 1000)
                        end_ms = int(end_time.timestamp() * 1000)
                        data["schedule"].append(
                            {
                                "ufCrm4Date": start_time.isoformat(),
                                "ufCrm4DateEnd": end_time.isoformat(),
                                "ufCrm4Intervals": [f"{start_ms}:{end_ms}"],
                            }
                        )
                        current_date += timedelta(days=1)
                    logger.debug(
                        f"Создано {len(data['schedule'])} дефолтных графиков для {spec_id}"
                    )

        logger.info("Графики и расписания специалистов обновлены")

    async def create_schedule_entry(self, fields: Dict, specialist=None) -> Dict:
        entityTypeId = constants.entityTypeId.appointment
        code = fields.get("ufCrm3Code") or (
            specialist.code if specialist and hasattr(specialist, "code") else None
        )
        code_id = constants.listFieldValues.appointment.idByCode.get(code, str(code))
        status_id = 50

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
