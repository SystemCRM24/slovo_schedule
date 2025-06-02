from datetime import datetime, timedelta
import logging
from pprint import pprint
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
    def __init__(self, data: RequestSchemaV2):
        self.initial_time = datetime.now(Settings.TIMEZONE) + timedelta(days=1)
        self.data = data
        self.specialists = self.create_specialists()
        self.total_required = sum(
            appoint.quantity for stage in self.data.data.values() for appoint in stage.data
        )
        self.min_break = 1
        self.max_break = 45 
        self.total_duration = sum(stage.duration * 7 for stage in self.data.data.values())
        logger.info(
            f"Инициализирован Handler: deal_id={self.data.deal_id}, user_id={self.data.user_id}, "
            f"всего занятий={self.total_required}, период={self.total_duration} дней"
        )

    def create_specialists(self) -> Tuple[Specialist]:
        """Создает специалистов для каждого назначения в каждом этапе."""
        specialists = []
        for stage_name, stage in self.data.data.items():
            for appoint in stage.data:
                specialists.append(
                    Specialist(self.initial_time, appoint.type, appoint.quantity, appoint.duration, stage.duration)
                )
        logger.info(f"Создано {len(specialists)} специалистов")
        return tuple(specialists)

    def get_child_appointments_on_day(self, user_id: int, dt: datetime) -> List[Dict]:
        """Получает все занятия ребенка за указанный день у всех специалистов."""
        target_day = dt.date()
        all_appointments = []
        for spec in self.specialists:
            for spec_id, data in spec.specialists_data.items():
                appointments = data.get("appointments", [])
                all_appointments.extend(
                    a for a in appointments
                    if a.get("user_id") == user_id
                    and datetime.fromisoformat(a["ufCrm3StartDate"]).date() == target_day
                )
        logger.debug(f"Найдено {len(all_appointments)} занятий ребенка на {target_day}")
        return all_appointments

    def get_specialist_appointments_on_day(self, appointments: List[Dict], dt: datetime) -> List[Dict]:
        """Получает все занятия специалиста за указанный день."""
        target_day = dt.date()
        return [
            a for a in appointments
            if datetime.fromisoformat(a["ufCrm3StartDate"]).date() == target_day
        ]

    def is_slot_ok(self, new_start: datetime, new_end: datetime, appointments: List[Dict]) -> bool:
        """Проверяет, подходит ли слот для специалиста: нет пересечений и есть минимальный перерыв."""
        for a in appointments:
            exist_start = datetime.fromisoformat(a["ufCrm3StartDate"])
            exist_end = datetime.fromisoformat(a["ufCrm3EndDate"])
            if not (new_end <= exist_start or new_start >= exist_end):
                logger.debug(f"Пересечение с {exist_start} — {exist_end}")
                return False
            if exist_end <= new_start < exist_end + timedelta(minutes=self.min_break):
                logger.debug(f"Слишком малый перерыв перед {new_start}")
                return False
            if exist_start > new_end and exist_start - new_end < timedelta(minutes=self.min_break):
                logger.debug(f"Слишком малый перерыв после {new_end}")
                return False
        return True

    def check_child_schedule(self, child_appointments: List[Dict], new_start: datetime, new_end: datetime) -> bool:
        """Проверяет расписание ребенка: не более 2 занятий в день, перерывы 15–45 минут, без пересечений."""
        if len(child_appointments) >= 2:
            logger.debug(f"Уже 2 занятия на {new_start.date()}")
            return False

        for existing in child_appointments:
            exist_start = datetime.fromisoformat(existing["ufCrm3StartDate"])
            exist_end = datetime.fromisoformat(existing["ufCrm3EndDate"])
            if not (new_end <= exist_start or new_start >= exist_end):
                logger.debug(f"Пересечение с {exist_start} — {exist_end}")
                return False

        if not child_appointments:
            return True

        existing = child_appointments[0]
        exist_start = datetime.fromisoformat(existing["ufCrm3StartDate"])
        exist_end = datetime.fromisoformat(existing["ufCrm3EndDate"])
        if new_end <= exist_start:
            gap = (exist_start - new_end).total_seconds() / 60
        elif new_start >= exist_end:
            gap = (new_start - exist_end).total_seconds() / 60
        else:
            return False

        if not (self.min_break <= gap <= self.max_break):
            logger.debug(f"Перерыв {gap} минут вне диапазона {self.min_break}–{self.max_break}")
            return False
        return True

    async def assign_appointment(self, chosen: Specialist, user_id: int, type_code: str, duration: int) -> Dict:
        """Назначает занятие, проверяя слоты у выбранного специалиста."""
        logger.info(f"Назначение занятия: type={type_code}, duration={duration}, user_id={user_id}")
        free_slots = chosen.get_all_free_slots()
        logger.debug(f"Найдено {len(free_slots)} слотов для типа {type_code}")

        for spec_id, slot in free_slots:
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            if slot_duration < duration:
                continue

            new_start = slot.start
            new_end = new_start + timedelta(minutes=duration)
            appointments = chosen.specialists_data.get(spec_id, {}).get("appointments", [])

            child_appointments_today = self.get_child_appointments_on_day(user_id, new_start)
            if not self.check_child_schedule(child_appointments_today, new_start, new_end):
                continue

            spec_appointments_today = self.get_specialist_appointments_on_day(appointments, new_start)
            if len(spec_appointments_today) >= 6:
                logger.debug(f"Специалист {spec_id} имеет 6 занятий на {new_start.date()}")
                continue

            if not self.is_slot_ok(new_start, new_end, appointments):
                continue
            children_id = await self.get_children_id(self.data.deal_id)
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

        logger.warning(f"Не найдено слотов у основного специалиста для {type_code}, ищем альтернативных")
        departments = await bitrix.get_all_departments()
        department_ids = [id for id, dept in departments.items() if type_code in dept.get("NAME", "")]
        
        date_start = self.initial_time.replace(hour=0, minute=0)
        date_end = date_start + timedelta(days=self.total_duration)
        date_start_iso = date_start.isoformat()
        date_end_iso = date_end.isoformat()

        try:
            cmd = {
                    f"dept_{dept_id}": BatchBuilder("user.get", {
                        "filter": {
                            "ACTIVE": True,
                            "%UF_DEPARTMENT": dept_id 
                        },
                        "order": {"ID": "ASC"}  
                    }).build()
                    for dept_id in department_ids
            }
            response = await bitrix.call_batch(cmd)
            specs = []
            for dept_id in department_ids:
                key = f"dept_{dept_id}"
                if key not in response:
                    continue
                if isinstance(response[key], list):
                    specs = response[key]
        except Exception as e:
            logger.error(f"Ошибка получения специалистов для отдела : {e}")
        for spec in specs:
            spec_id = spec.get("ID")
            if not spec_id or spec_id in chosen.specialists_data:
                continue
            chosen.specialists_data[spec_id] = {"schedule": [], "appointments": []}
            cmd = {
                f"schedule_{spec_id}": BatchBuilder("crm.item.list", {
                    "entityTypeId": 1042,
                    "filter": {">=ufCrm4Date": date_start_iso, "<ufCrm4Date": date_end_iso, "assignedById": spec_id},
                }).build(),
                f"appointments_{spec_id}": BatchBuilder("crm.item.list", {
                    "entityTypeId": 1036,
                    "filter": {">=ufCrm3StartDate": date_start_iso, "<ufCrm3StartDate": date_end_iso, "assignedById": spec_id},
                }).build()
            }
            try:
                response = await bitrix.call_batch(cmd)
                chosen.specialists_data[spec_id]["schedule"] = response.get(f"schedule_{spec_id}", {}).get("items", [])
                chosen.specialists_data[spec_id]["appointments"] = response.get(f"appointments_{spec_id}", {}).get("items", [])
            except Exception as e:
                logger.error(f"Ошибка загрузки данных для {spec_id}: {e}")
                continue
            free_slots = chosen.get_all_free_slots()
            for alt_spec_id, slot in free_slots:
                slot_duration = (slot.end - slot.start).total_seconds() / 60
                if slot_duration < duration:
                    continue
                new_start = slot.start
                new_end = new_start + timedelta(minutes=duration)
                appointments = chosen.specialists_data.get(alt_spec_id, {}).get("appointments", [])
                child_appointments_today = self.get_child_appointments_on_day(user_id, new_start)
                if not self.check_child_schedule(child_appointments_today, new_start, new_end):
                    continue
                spec_appointments_today = self.get_specialist_appointments_on_day(appointments, new_start)
                if len(spec_appointments_today) >= 6:
                    continue
                if not self.is_slot_ok(new_start, new_end, appointments):
                    continue
                children_id = await self.get_children_id(self.data.deal_id)
                fields = {
                    "assignedById": int(alt_spec_id),
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
                chosen.specialists_data[alt_spec_id]["appointments"] = appointments
                logger.info(f"Назначено занятие для {alt_spec_id} на {new_start} — {new_end}")
                return fields
        logger.error(f"Не удалось назначить занятие для {type_code}")
        return None

    async def run(self) -> Dict:
        """Запускает процесс распределения занятий."""
        logger.info("Запуск распределения занятий")
        await self.update_specialists_info()
        await self.update_specialists_schedules()

        user_id = self.data.user_id
        appointments_to_create = []
        failed_appointments = []

        for stage_name, stage in self.data.data.items():
            logger.info(f"Обработка этапа: {stage_name}")
            for appoint in stage.data:
                type_code = appoint.type
                quantity = appoint.quantity
                duration = appoint.duration
                logger.info(f"Планирование {quantity} занятий типа {type_code}")

                candidates = [spec for spec in self.specialists if spec.code == type_code]
                if not candidates:
                    logger.error(f"Нет специалистов для типа {type_code}")
                    return {"error": f"Нет специалистов для типа {type_code}"}

                for _ in range(quantity):
                    for candidate in candidates:
                        fields = await self.assign_appointment(candidate, user_id, type_code, duration)
                        if fields:
                            appointments_to_create.append(fields)
                            break
                    else:
                        failed_appointments.append({"type": type_code, "duration": duration})
                        logger.warning(f"Не удалось запланировать занятие типа {type_code}")

        if failed_appointments:
            error_msg = "Не удалось запланировать занятия:\n" + "\n".join(
                f"- Тип: {fa['type']}, Длительность: {fa['duration']} мин" for fa in failed_appointments
            )
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info(f"Создание {len(appointments_to_create)} занятий в Bitrix")
        cmd = {}
        children_id = await self.get_children_id(self.data.deal_id)
        for i, fields in enumerate(appointments_to_create):
            code_id = constants.listFieldValues.appointment.idByCode.get(fields["ufCrm3Code"], fields["ufCrm3Code"])
            cmd[f"create_{i}"] = BatchBuilder("crm.item.add", {
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
                }
            }).build()

        created_ids = []
        try:
            response = await bitrix.call_batch(cmd)
            for i, fields in enumerate(appointments_to_create):
                item = response.get(f"create_{i}", {}).get("item", {})
                if item.get("id"):
                    fields["id"] = item["id"]
                    created_ids.append(item["id"])
                else:
                    raise Exception(f"Не удалось создать занятие {i}: {response.get(f'create_{i}')}")
            logger.info("Все занятия успешно созданы")
            return {"appointments": appointments_to_create}
        except Exception as e:
            logger.error(f"Ошибка создания занятий: {e}")
            cmd = {
                f"delete_appointment_{appointment_id}": {
                    "method": "crm.item.delete",
                    "params": {
                        "id": appointment_id,
                        "entityTypeId": constants.entityTypeId.appointment
                    }
                }
                for appointment_id in created_ids
            }
            await bitrix.call_batch(cmd)
            return {"error": f"Ошибка создания занятий: {str(e)}"}

    async def update_specialists_info(self):
        """Обновляет информацию о специалистах."""
        logger.info("Обновление информации о специалистах")
        departments = await bitrix.get_all_departments()
        cmd = {f"spec_{i}": s.get_specialists_info_batch(departments) for i, s in enumerate(self.specialists)}
        try:
            response = await bitrix.call_batch(cmd)
            for i, spec in enumerate(self.specialists):
                specs_list = response.get(f"spec_{i}", [])
                spec.possible_specs = specs_list if isinstance(specs_list, list) else []
                spec.specialists_data = {str(s["ID"]): {"schedule": [], "appointments": []} for s in spec.possible_specs if "ID" in s}
                if not spec.possible_specs:
                    logger.warning(f"Нет специалистов для {spec.code}")
        except Exception as e:
            logger.error(f"Ошибка получения информации о специалистах: {e}")
            for spec in self.specialists:
                spec.possible_specs = []
                spec.specialists_data = {}

    async def get_children_id(self, deal_id: int) -> Optional[int]:
        cmd = {
            "deal_info": BatchBuilder("crm.deal.list", {
                "filter": {"ID": deal_id},
                "select": ["*"]
            }).build()
        }
        try:
            response = await bitrix.call_batch(cmd=cmd)
            if response.get("deal_info"):
                contact_id = response["deal_info"][0]["CONTACT_ID"]
                if contact_id != "": 
                    try:
                        return int(contact_id)
                    except ValueError as e:
                        return None
        except Exception as e:
            print(f"Error getting deal info: {e}")
            return None

    async def update_specialists_schedules(self):
        """Обновляет графики специалистов на весь период."""
        logger.info("Обновление графиков специалистов")
        cmd = {}
        date_start = self.initial_time.replace(hour=0, minute=0)
        date_end = date_start + timedelta(days=self.total_duration)
        date_start_iso = date_start.isoformat()
        date_end_iso = date_end.isoformat()
        mapping = {}

        # Подготовка команд для получения данных из Bitrix
        for spec in self.specialists:
            if not spec.possible_specs:
                continue
            for ps in spec.possible_specs:
                spec_id = ps.get("ID")
                if not spec_id:
                    continue
                if spec_id not in spec.specialists_data:
                    spec.specialists_data[spec_id] = {"schedule": [], "appointments": []}
                idx = len(cmd)
                cmd[f"schedule_{idx}"] = BatchBuilder("crm.item.list", {
                    "entityTypeId": 1042,
                    "filter": {">=ufCrm4Date": date_start_iso, "<ufCrm4Date": date_end_iso, "assignedById": spec_id},
                }).build()
                mapping[f"schedule_{idx}"] = (spec, spec_id, "schedule")
                cmd[f"appointments_{idx}"] = BatchBuilder("crm.item.list", {
                    "entityTypeId": 1036,
                    "filter": {">=ufCrm3StartDate": date_start_iso, "<ufCrm3StartDate": date_end_iso, "assignedById": spec_id},
                }).build()
                mapping[f"appointments_{idx}"] = (spec, spec_id, "appointments")

        if not cmd:
            logger.error("Нет данных для загрузки графиков")
            return

        try:
            response = await bitrix.call_batch(cmd)

            if not isinstance(response, dict):
                raise ValueError("Некорректный ответ от Bitrix: ожидался словарь")
            
            for key, (spec, spec_id, typ) in mapping.items():
                result = response.get(key, {})
                items = result.get("items", [])

                if isinstance(items, list):
                    spec.specialists_data[spec_id][typ] = items
                else:
                    logger.error(f"Некорректный формат 'items' для {key}: {items}")
                    spec.specialists_data[spec_id][typ] = []
                if not items and typ == "schedule":
                    logger.warning(f"Нет графика для специалиста {spec_id}")
        except Exception as e:
            logger.error(f"Ошибка загрузки графиков: {e}")
            for spec in self.specialists:
                for spec_id in spec.specialists_data:
                    spec.specialists_data[spec_id] = {"schedule": [], "appointments": []}