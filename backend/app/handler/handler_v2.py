from datetime import datetime, timedelta
import logging
from typing import Dict, Dict, List, Tuple
from app.settings import Settings
from app.schemas import RequestSchemaV2
from app import bitrix
from app.utils import BatchBuilder
from api.constants import constants
from .specialist import Specialist

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
        self.min_break = 15
        self.max_break = 45
        logger.info(
            f"Инициализирован Handler для deal_id={self.data.deal_id}, user_id={self.data.user_id}, "
            f"всего занятий={self.total_required}"
        )

    def create_specialists(self) -> Tuple[Specialist]:
        specialists = []
        for stage_name, stage in self.data.data.items():
            for appoint in stage.data:
                specialists.append(
                    Specialist(self.initial_time, appoint.type, appoint.quantity, appoint.duration, stage.duration)
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

    async def assign_appointment(self, chosen: Specialist, user_id: int, appoint, type_code: str, duration: int) -> Dict:
        logger.info(f"Планирование занятия: type={type_code}, duration={duration}, user_id={user_id}")
        free_slots = chosen.get_all_free_slots()
        logger.debug(f"Найдено {len(free_slots)} свободных слотов для специалиста типа {type_code}")

        if free_slots:
            for spec_id, slot in free_slots:
                slot_duration = (slot.end - slot.start).total_seconds() / 60
                if slot_duration < duration:
                    logger.debug(f"Слот {slot.start} — {slot.end} слишком короткий ({slot_duration} мин < {duration} мин)")
                    continue

                data = chosen.specialists_data.get(spec_id, {})
                appointments = data.get("appointments", [])

                new_start = slot.start
                new_end = new_start + timedelta(minutes=duration)

                child_appointments_today = self.get_appointments_on_day(appointments, user_id, new_start)
                if len(child_appointments_today) >= 2:
                    logger.debug(f"Отклонено: уже 2 занятия у ребенка в день {new_start.date()}")
                    continue

                spec_appointments_today = self.get_specialist_appointments_on_day(appointments, new_start)
                if len(spec_appointments_today) >= 6:
                    logger.debug(f"Отклонено: уже 6 занятий у специалиста {spec_id} в день {new_start.date()}")
                    continue

                if not self.is_slot_ok(new_start, new_end, appointments, min_break=self.min_break):
                    logger.debug(f"Отклонено: не подходит из-за минимального перерыва")
                    continue

                user_appointments_same_day = [
                    a for a in appointments if a["user_id"] == user_id and datetime.fromisoformat(a["ufCrm3StartDate"]).date() == new_start.date()
                ]
                new_appt = {
                    "ufCrm3StartDate": new_start.isoformat(),
                    "ufCrm3EndDate": new_end.isoformat(),
                    "user_id": user_id,
                    "ufCrm3Type": type_code,
                }
                all_user_same_day = user_appointments_same_day + [new_appt]
                sorted_all = sorted(all_user_same_day, key=lambda x: datetime.fromisoformat(x["ufCrm3StartDate"]))
                ok = True
                for i in range(1, len(sorted_all)):
                    prev_end = datetime.fromisoformat(sorted_all[i - 1]["ufCrm3EndDate"])
                    curr_start = datetime.fromisoformat(sorted_all[i]["ufCrm3StartDate"])
                    gap = (curr_start - prev_end).total_seconds() / 60
                    if gap > self.max_break:
                        ok = False
                        logger.debug(f"Слот {new_start} — {new_end} создает слишком большой перерыв > {self.max_break} мин")
                        break
                if not ok:
                    continue

                if type_code == "R":
                    r_appointments_today = [a for a in child_appointments_today if a.get("ufCrm3Type") == "R"]
                    if len(r_appointments_today) >= 2:
                        logger.debug(f"У ребенка уже 2 занятия типа R в день {new_start.date()}")
                        continue

                fields = {
                    "assignedById": int(spec_id),
                    "ufCrm3StartDate": new_start.isoformat(),
                    "ufCrm3EndDate": new_end.isoformat(),
                    "ufCrm3ParentDeal": self.data.deal_id,
                    "ufCrm3Child": user_id,
                    "user_id": user_id,
                    "ufCrm3Type": type_code,
                    "ufCrm3Code": type_code,
                }
                appointments.append(new_appt)
                chosen.specialists_data[spec_id]["appointments"] = appointments
                logger.info(f"Запланировано занятие для специалиста {spec_id} на {new_start} — {new_end}")
                return fields

        # Поиск альтернативных специалистов
        logger.warning(f"Нет свободных слотов для типа {type_code}, ищем альтернативных специалистов")
        departments = await bitrix.get_all_departments()
        department_ids = []
        for id, dept in departments.items():
            if dept.get("NAME") == type_code or type_code in dept.get("NAME", ""):
                department_ids.append(id)

        total_duration = sum(stage.duration * 7 for stage in self.data.data.values())  # 56 дней
        for dept_id in department_ids:
            for extra_days in range(0, total_duration, 7):
                date_start = self.initial_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=extra_days)
                date_end = date_start + timedelta(days=total_duration)
                date_start_iso = date_start.isoformat()
                date_end_iso = date_end.isoformat()

                cmd = {
                    "get_specs": BatchBuilder(
                        "user.get",
                        {"filter": {"ACTIVE": True, "UF_DEPARTMENT": dept_id}}
                    ).build()
                }
                try:
                    response = await bitrix.call_batch(cmd)
                    alternative_specs = response.get("result", {}).get("result", {}).get("get_specs", [])
                    if isinstance(alternative_specs, dict):
                        alternative_specs = list(alternative_specs.values())
                    if not isinstance(alternative_specs, list):
                        logger.error(f"Некорректный формат ответа для отдела {dept_id}: {alternative_specs}")
                        alternative_specs = []
                    logger.debug(f"Найдено {len(alternative_specs)} альтернативных специалистов для отдела {dept_id}")
                except Exception as e:
                    logger.error(f"Ошибка при получении альтернативных специалистов для отдела {dept_id}: {e}")
                    continue

                for spec in alternative_specs:
                    spec_id = spec.get("ID")
                    if not spec_id:
                        continue
                    if spec_id not in chosen.specialists_data:
                        chosen.specialists_data[spec_id] = {"schedule": [], "appointments": []}
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
                                "order": {"ufCrm4Date": "ASC"},
                            }
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
                                "order": {"ufCrm3StartDate": "ASC"},
                            }
                        ).build()
                    }
                    try:
                        response = await bitrix.call_batch(cmd)
                        batch_result = response.get("result", {}).get("result", {})
                        schedule_data = batch_result.get(f"schedule_{spec_id}", {})
                        chosen.specialists_data[str(spec_id)]["schedule"] = schedule_data.get("items", []) if isinstance(schedule_data, dict) else []
                        appointments_data = batch_result.get(f"appointments_{spec_id}", {})
                        chosen.specialists_data[str(spec_id)]["appointments"] = appointments_data.get("items", []) if isinstance(appointments_data, dict) else []
                        logger.debug(f"Загружены графики и занятия для специалиста {spec_id}")
                    except Exception as e:
                        logger.error(f"Ошибка при получении данных для специалиста {spec_id}: {e}")
                        continue

                    free_slots = chosen.get_all_free_slots()
                    if free_slots:
                        for alt_spec_id, slot in free_slots:
                            slot_duration = (slot.end - slot.start).total_seconds() / 60
                            if slot_duration < duration:
                                continue
                            data = chosen.specialists_data.get(alt_spec_id, {})
                            appointments = data.get("appointments", [])
                            new_start = slot.start
                            new_end = new_start + timedelta(minutes=duration)
                            child_appointments_today = self.get_appointments_on_day(appointments, user_id, new_start)
                            if len(child_appointments_today) >= 2:
                                continue
                            spec_appointments_today = self.get_specialist_appointments_on_day(appointments, new_start)
                            if len(spec_appointments_today) >= 6:
                                continue
                            if not self.is_slot_ok(new_start, new_end, appointments, min_break=self.min_break):
                                continue
                            user_appointments_same_day = [
                                a for a in appointments if a["user_id"] == user_id and datetime.fromisoformat(a["ufCrm3StartDate"]).date() == new_start.date()
                            ]
                            new_appt = {
                                "ufCrm3StartDate": new_start.isoformat(),
                                "ufCrm3EndDate": new_end.isoformat(),
                                "user_id": user_id,
                                "ufCrm3Type": type_code,
                            }
                            all_user_same_day = user_appointments_same_day + [new_appt]
                            sorted_all = sorted(all_user_same_day, key=lambda x: datetime.fromisoformat(x["ufCrm3StartDate"]))
                            ok = True
                            for i in range(1, len(sorted_all)):
                                prev_end = datetime.fromisoformat(sorted_all[i - 1]["ufCrm3EndDate"])
                                curr_start = datetime.fromisoformat(sorted_all[i]["ufCrm3StartDate"])
                                gap = (curr_start - prev_end).total_seconds() / 60
                                if gap > self.max_break:
                                    ok = False
                                    break
                            if not ok:
                                continue
                            if type_code == "R":
                                r_appointments_today = [a for a in child_appointments_today if a.get("ufCrm3Type") == "R"]
                                if len(r_appointments_today) >= 2:
                                    continue
                            fields = {
                                "assignedById": int(alt_spec_id),
                                "ufCrm3StartDate": new_start.isoformat(),
                                "ufCrm3EndDate": new_end.isoformat(),
                                "ufCrm3ParentDeal": self.data.deal_id,
                                "ufCrm3Child": user_id,
                                "user_id": user_id,
                                "ufCrm3Type": type_code,
                                "ufCrm3Code": type_code,
                            }
                            appointments.append(new_appt)
                            chosen.specialists_data[alt_spec_id]["appointments"] = appointments
                            logger.info(f"Запланировано занятие для альтернативного специалиста {alt_spec_id} на {new_start} — {new_end}")
                            return fields
        logger.warning(f"Не удалось найти подходящий слот для type={type_code}, user_id={user_id}")
        return None

    async def run(self) -> Dict:
        logger.info("Запуск распределения занятий")
        await self.update_specialists_info()
        await self.update_specialists_schedules()

        user_id = self.data.user_id
        appointments_to_create = []
        created_ids = []
        total_max_days = sum(stage.duration * 7 for stage in self.data.data.values())  # 56 дней
        current_day = 0

        for stage_name, stage in self.data.data.items():
            logger.info(f"Обработка этапа: {stage_name} (в рамках {total_max_days} дней)")

            for appoint in stage.data:
                type_code = appoint.type
                quantity = appoint.quantity
                duration = appoint.duration
                logger.info(f"Планирование {quantity} занятий типа {type_code} длительностью {duration} минут")

                candidates = [spec for spec in self.specialists if spec.code == type_code]
                if not candidates:
                    logger.error(f"Не найдено специалистов для типа {type_code}")
                    return {"error": f"Не найдено специалистов для типа {type_code}"}

                for _ in range(quantity):
                    if current_day >= total_max_days:
                        logger.error(f"Превышен общий лимит дней ({total_max_days})")
                        return {"error": f"Не удалось запланировать все занятия за {total_max_days} дней"}

                    for candidate in candidates:
                        fields = await self.assign_appointment(candidate, user_id, appoint, type_code, duration)
                        if fields:
                            appointments_to_create.append(fields)
                            break
                    else:
                        logger.warning(f"Не удалось найти слот для типа {type_code} на день {self.initial_time.date()}")
                        self.initial_time += timedelta(days=1)
                        current_day += 1
                        await self.update_specialists_schedules()
                        continue

        if len(appointments_to_create) != self.total_required:
            logger.error(f"Запланировано {len(appointments_to_create)} из {self.total_required} занятий")
            return {"error": "Не удалось запланировать все занятия"}

        logger.info(f"Создание {len(appointments_to_create)} занятий в Bitrix")
        cmd = {}
        for i, fields in enumerate(appointments_to_create):
            code = fields.get("ufCrm3Code", "")
            code_id = constants.listFieldValues.appointment.idByCode.get(code, str(code))
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
            cmd[f"create_{i}"] = BatchBuilder(
                "crm.item.add",
                {
                    "entityTypeId": constants.entityTypeId.appointment,
                    "fields": batch_fields,
                },
            ).build()

        try:
            response = await bitrix.call_batch(cmd)
            logger.info(f"Ответ от Bitrix: {response}")

            for i, fields in enumerate(appointments_to_create):
                result = response.get(f"create_{i}", {})
                item = result.get("result", {}).get("item", {})
                item_id = item.get("id")
                if item_id:
                    fields["id"] = item_id
                    created_ids.append(item_id)
                else:
                    logger.error(f"Не удалось создать занятие {i}: {result}")
                    for created_id in created_ids:
                        await bitrix.call_batch({
                            f"delete_{created_id}": BatchBuilder(
                                "crm.item.delete",
                                {
                                    "id": created_id,
                                    "entityTypeId": constants.entityTypeId.appointment,
                                }
                            ).build()
                        })
                        logger.info(f"Удалено занятие с ID {created_id}")
                    return {"error": "Не удалось создать все занятия, выполнен откат"}

            logger.info("Все занятия успешно созданы в Bitrix")
            return {"appointments": appointments_to_create}

        except Exception as e:
            logger.error(f"Ошибка при создании занятий: {e}")
            for created_id in created_ids:
                await bitrix.call_batch({
                    f"delete_{created_id}": BatchBuilder(
                        "crm.item.delete",
                        {
                            "id": created_id,
                            "entityTypeId": constants.entityTypeId.appointment,
                        }
                    ).build()
                })
                logger.info(f"Удалено занятие с ID {created_id}")
            return {"error": f"Ошибка при создании занятий: {str(e)}"}

    async def update_specialists_info(self):
        logger.info("Обновление информации о специалистах")
        departments = await bitrix.get_all_departments()
        batches = tuple(
            s.get_specialists_info_batch(departments) for s in self.specialists
        )
        cmd = {f"spec_{index}": value for index, value in enumerate(batches)}
        try:
            response = await bitrix.call_batch(cmd)
            logger.debug(f"Ответ Bitrix в update_specialists_info: {response}")
            
            # Основное изменение - правильная обработка ответа
            batch_results = response.get('result', {}).get('result', {})
            
            for index, spec in enumerate(self.specialists):
                spec_key = f"spec_{index}"
                specs_list = batch_results.get(spec_key, [])
                
                if not isinstance(specs_list, list):
                    logger.error(f"Некорректный формат ответа для {spec_key}: {specs_list}")
                    specs_list = []
                    
                spec.possible_specs = specs_list
                # Инициализация specialists_data для каждого найденного специалиста
                spec.specialists_data = {
                    str(spec_data['ID']): {
                        "schedule": [],
                        "appointments": []
                    } 
                    for spec_data in specs_list 
                    if 'ID' in spec_data
                }
                
                logger.debug(
                    f"Загружено {len(spec.possible_specs)} специалистов для code={spec.code}"
                )
                if not spec.possible_specs:
                    logger.warning(f"Не найдено специалистов для code={spec.code}")
                    
        except Exception as e:
            logger.error(f"Ошибка при получении информации о специалистах: {e}")
            for spec in self.specialists:
                spec.possible_specs = []
                spec.specialists_data = {}
                
        logger.info("Информация о специалистах обновлена")

    async def update_specialists_schedules(self):
        logger.info("Обновление графиков специалистов")
        cmd = {}
        date_start = self.initial_time.replace(hour=0, minute=0, second=0, microsecond=0)
        total_duration = sum(stage.duration * 7 for stage in self.data.data.values())  # 56 дней
        date_end = date_start + timedelta(days=total_duration)
        date_start_iso = date_start.isoformat()
        date_end_iso = date_end.isoformat()
        batch_index = 0
        mapping = {}

        for spec in self.specialists:
            if not spec.possible_specs:
                logger.error(f"Нет специалистов для code={spec.code}, пропускаю")
                continue
            for possible_spec in spec.possible_specs:
                specialist_id = possible_spec.get("ID")
                if not specialist_id:
                    logger.warning(f"Отсутствует ID специалиста для code={spec.code}")
                    continue
                if specialist_id not in spec.specialists_data:
                    spec.specialists_data[specialist_id] = {"schedule": [], "appointments": []}

                cmd[f"schedule_{batch_index}"] = BatchBuilder(
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
                mapping[f"schedule_{batch_index}"] = (spec, specialist_id, "schedule")
                batch_index += 1

                cmd[f"appointments_{batch_index}"] = BatchBuilder(
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
                mapping[f"appointments_{batch_index}"] = (spec, specialist_id, "appointments")
                batch_index += 1

        if not cmd:
            logger.error("Нет батчей для запроса графиков, возможно, нет специалистов")
            return

        try:
            response = await bitrix.call_batch(cmd)
            logger.debug(f"Ответ Bitrix в update_specialists_schedules: {response}")
            if not response:
                logger.error("Пустой ответ от Bitrix в update_specialists_schedules")
                return
            for key, (spec, specialist_id, typ) in mapping.items():
                result = response.get(key, {}).get("result", {}).get("items", [])
                if not isinstance(result, list):
                    logger.error(f"Некорректный формат данных для специалиста {specialist_id}: {result}")
                    result = []
                spec.specialists_data[specialist_id][typ] = result
                logger.debug(f"Загружено {len(result)} {typ} для специалиста {specialist_id}")
        except Exception as e:
            logger.error(f"Ошибка при получении графиков: {e}")
            for spec in self.specialists:
                for spec_id in spec.specialists_data:
                    spec.specialists_data[spec_id]["schedule"] = []
                    spec.specialists_data[spec_id]["appointments"] = []

        for spec in self.specialists:
            for spec_id, data in spec.specialists_data.items():
                if not data["schedule"]:
                    logger.error(f"Нет графика для специалиста {spec_id}, пропускаю")
                    data["schedule"] = []  # Не создаём дефолтные графики

            logger.info("Графики и расписания специалистов обновлены")
            logger.info("Обновление графиков специалистов")
            cmd = {}
            date_start = self.initial_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            max_duration = max(
                stage.duration * 7 for stage in self.data.data.values()
            )
            date_end = date_start + timedelta(days=max_duration)
            date_start_iso = date_start.isoformat()
            date_end_iso = date_end.isoformat()
            batch_index = 0
            mapping = {}

            for spec in self.specialists:
                for possible_spec in spec.possible_specs:
                    specialist_id = possible_spec.get("ID")
                    if specialist_id and specialist_id not in spec.specialists_data:
                        spec.specialists_data[specialist_id] = {
                            "schedule": [],
                            "appointments": [],
                        }

            for spec in self.specialists:
                for possible_spec in spec.possible_specs:
                    specialist_id = possible_spec.get("ID")
                    if not specialist_id:
                        logger.warning(f"Отсутствует ID специалиста для code={spec.code}")
                        continue

                    cmd[f"schedule_{batch_index}"] = BatchBuilder(
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
                    mapping[f"schedule_{batch_index}"] = (spec, specialist_id, "schedule")
                    batch_index += 1

                    cmd[f"appointments_{batch_index}"] = BatchBuilder(
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
                    mapping[f"appointments_{batch_index}"] = (spec, specialist_id, "appointments")
                    batch_index += 1

            if cmd:
                try:
                    response = await bitrix.call_batch(cmd)
                    logger.debug(f"Ответ Bitrix в update_specialists_schedules: {response}")
                    if not response:
                        logger.error("Пустой ответ от Bitrix в update_specialists_schedules")
                        return
                    for key, (spec, specialist_id, typ) in mapping.items():
                        result = response.get(key, {}).get("result", {}).get("items", [])
                        if not isinstance(result, list):
                            logger.error(
                                f"Некорректный формат данных для специалиста {specialist_id}: {result}"
                            )
                            result = []
                        spec.specialists_data[specialist_id][typ] = result
                        logger.debug(
                            f"Загружено {len(result)} {typ} для специалиста {specialist_id}"
                        )
                except Exception as e:
                    logger.error(f"Ошибка при получении графиков: {e}")
                    for spec in self.specialists:
                        for spec_id in spec.specialists_data:
                            spec.specialists_data[spec_id]["schedule"] = []
                            spec.specialists_data[spec_id]["appointments"] = []
            else:
                logger.warning("Нет батчей для запроса графиков")

            for spec in self.specialists:
                for spec_id, data in spec.specialists_data.items():
                    if not data["schedule"]:
                        logger.warning(f"Нет графика для специалиста {spec_id}, создаю дефолтные")
                        data["schedule"] = []
                        current_date = date_start
                        while current_date <= date_end:
                            start_time = current_date.replace(hour=9, minute=0, second=0, microsecond=0)
                            end_time = current_date.replace(hour=18, minute=0, second=0, microsecond=0)
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
                        logger.debug(f"Создано {len(data['schedule'])} дефолтных графиков для {spec_id}")

            logger.info("Графики и расписания специалистов обновлены")