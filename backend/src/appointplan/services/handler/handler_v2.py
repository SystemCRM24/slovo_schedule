from datetime import datetime, timedelta, timezone
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
    """Обработчик для распределения занятий на основе данных запроса версии 2."""

    def __init__(self, data: RequestSchemaV2):
        self.initial_time = datetime.now(Settings.TIMEZONE) + timedelta(days=1)
        self.data = data
        self.specialists = self._create_specialists()
        self.min_break = 1  # минуты между занятиями
        self.total_duration = sum(
            stage.duration * 7 for stage in self.data.data.values()
        )
        logger.info(
            f"Инициализирован Handler: deal_id={self.data.deal_id}, user_id={self.data.user_id}, "
            f"период={self.total_duration} дней"
        )

    def _create_specialists(self) -> Tuple[Specialist]:
        specialists = []
        for stage in self.data.data.values():
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
        return tuple(specialists)

    def _get_child_intervals(
        self, user_id: int, date: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """
        Все уже спланированные ребенку занятия (любого специалиста) на date.
        """
        target_day = date.date()
        intervals = []
        for spec in self.specialists:
            for spec_id, data in spec.specialists_data.items():
                for a in data.get("appointments", []):
                    if a["user_id"] != user_id:
                        continue
                    s = datetime.fromisoformat(a["ufCrm3StartDate"])
                    if s.date() != target_day:
                        continue
                    e = datetime.fromisoformat(a["ufCrm3EndDate"])
                    intervals.append((s, e))
        return sorted(intervals, key=lambda x: x[0])

    async def _try_place_in_schedule(
        self,
        spec: Specialist,
        spec_id: str,
        user_id: int,
        type_code: str,
        duration: int,
        date: datetime,
        child_intervals: List[Tuple[datetime, datetime]],
    ) -> Optional[Dict]:
        """
        Берем из spec.specialists_data[spec_id]['schedule'] список рабочих интервалов
        (ufCrm4Date, ufCrm4Intervals) на date, и пытаемся вставить занятие длиной duration,
        начиная с момента, следующего за последним занятием любого специалиста у ребенка.
        """
        # 1) Находим последний конец из child_intervals
        if child_intervals:
            last_end = max(e for (_, e) in child_intervals) + timedelta(
                minutes=self.min_break
            )
        else:
            last_end = datetime.combine(date.date(), datetime.min.time()).replace(
                tzinfo=self.initial_time.tzinfo
            )

        # 2) Собираем рабочие интервалы (ufCrm4Intervals) в этот день
        ws: List[Tuple[datetime, datetime]] = []
        for s in spec.specialists_data[spec_id].get("schedule", []):
            work_start = datetime.fromisoformat(s["ufCrm4Date"])
            if work_start.date() != date.date():
                continue
            intervals = s.get("ufCrm4Intervals", [])
            if not intervals:
                continue
            try:
                ms_start, ms_end = intervals[0].split(":")
                sec_start = int(ms_start) / 1000
                sec_end = int(ms_end) / 1000
                tz = work_start.tzinfo or timezone.utc
                ws.append(
                    (
                        datetime.fromtimestamp(sec_start, tz),
                        datetime.fromtimestamp(sec_end, tz),
                    )
                )
            except Exception:
                continue

        ws.sort(key=lambda x: x[0])

        # 3) Список уже назначенных занятий этого специалиста
        spec_appts: List[Tuple[datetime, datetime]] = []
        for a in spec.specialists_data[spec_id].get("appointments", []):
            appt_start = datetime.fromisoformat(a["ufCrm3StartDate"])
            if appt_start.date() != date.date():
                continue
            appt_end = datetime.fromisoformat(a["ufCrm3EndDate"])
            spec_appts.append((appt_start, appt_end))
        spec_appts.sort(key=lambda x: x[0])

        # 4) Перебираем рабочие интервалы
        for work_start, work_end in ws:
            cursor = max(work_start, last_end)
            # Если курсор внутри уже занятого у специалиста, сдвигаем
            for ps, pe in spec_appts:
                if ps <= cursor < pe:
                    cursor = pe + timedelta(minutes=self.min_break)
            while cursor + timedelta(minutes=duration) <= work_end:
                new_start = cursor
                new_end = new_start + timedelta(minutes=duration)

                # 4.1) Проверяем пересечение у специалиста
                conflict = False
                for ps, pe in spec_appts:
                    if not (new_end <= ps or new_start >= pe):
                        conflict = True
                        cursor = pe + timedelta(minutes=self.min_break)
                        break
                if conflict:
                    continue

                # 4.2) Учитывая, что курсор уже >= last_end, новых проверок по ребенку не нужно

                # 4.3) Проверяем лимит у специалиста: не более 6 занятий в день
                if len(spec_appts) >= 6:
                    return None

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

                spec.specialists_data[spec_id]["appointments"].append(
                    {
                        "ufCrm3StartDate": new_start.isoformat(),
                        "ufCrm3EndDate": new_end.isoformat(),
                        "user_id": user_id,
                        "ufCrm3Type": type_code,
                    }
                )
                spec_appts.append((new_start, new_end))
                spec_appts.sort(key=lambda x: x[0])

                logger.info(f"Назначено занятие у {spec_id} на {new_start}–{new_end}")
                return fields

        return None

    async def update_specialists_info(self) -> None:
        """Получаем список возможных специалистов и инициализируем specialists_data."""
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
        except Exception as e:
            logger.error(f"Ошибка получения специалистов: {e}")
            for spec in self.specialists:
                spec.possible_specs = []
                spec.specialists_data = {}

    async def _update_specialists_schedules(self) -> None:
        """Загружаем из Битрикса расписание (schedule) и имеющиеся записи (appointments)."""
        cmd = {}
        date_start = self.initial_time.replace(hour=0, minute=0)
        date_end = date_start + timedelta(days=self.total_duration)
        ds = date_start.isoformat()
        de = date_end.isoformat()
        mapping = {}

        for spec in self.specialists:
            for ps in getattr(spec, "possible_specs", []):
                sid = ps.get("ID")
                if not sid:
                    continue
                if sid not in spec.specialists_data:
                    spec.specialists_data[sid] = {"schedule": [], "appointments": []}
                idx = len(cmd)
                cmd[f"schedule_{idx}"] = BatchBuilder(
                    "crm.item.list",
                    {
                        "entityTypeId": 1042,
                        "filter": {
                            ">=ufCrm4Date": ds,
                            "<ufCrm4Date": de,
                            "assignedById": sid,
                        },
                    },
                ).build()
                mapping[f"schedule_{idx}"] = (spec, sid, "schedule")

                cmd[f"appointments_{idx}"] = BatchBuilder(
                    "crm.item.list",
                    {
                        "entityTypeId": 1036,
                        "filter": {
                            ">=ufCrm3StartDate": ds,
                            "<ufCrm3StartDate": de,
                            "assignedById": sid,
                        },
                    },
                ).build()
                mapping[f"appointments_{idx}"] = (spec, sid, "appointments")

        if not cmd:
            return

        try:
            response = await bitrix.call_batch(cmd)
            for key, (spec, sid, typ) in mapping.items():
                items = response.get(key, {}).get("items", [])
                spec.specialists_data[sid][typ] = (
                    items if isinstance(items, list) else []
                )
        except Exception as e:
            logger.error(f"Ошибка загрузки графиков: {e}")
            for spec in self.specialists:
                for sid in spec.specialists_data:
                    spec.specialists_data[sid] = {"schedule": [], "appointments": []}

    async def _get_children_id(self, deal_id: int) -> Optional[int]:
        cmd = {
            "deal_info": BatchBuilder(
                "crm.deal.list", {"filter": {"ID": deal_id}, "select": ["*"]}
            ).build()
        }
        try:
            resp = await bitrix.call_batch(cmd)
            info = resp.get("deal_info", [])
            if info:
                cid = info[0].get("CONTACT_ID")
                return int(cid) if cid else None
        except Exception as e:
            logger.error(f"Ошибка получения ID ребенка: {e}")
        return None

    async def _create_appointments_batch(
        self, to_create: List[Dict]
    ) -> Tuple[List[str], List[Dict]]:
        cmd = {}
        children_id = await self._get_children_id(self.data.deal_id)
        for i, fields in enumerate(to_create):
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

        created = []
        try:
            resp = await bitrix.call_batch(cmd)
            for i, fields in enumerate(to_create):
                item = resp.get(f"create_{i}", {}).get("item", {})
                if item.get("id"):
                    fields["id"] = item["id"]
                    created.append(item["id"])
                else:
                    raise Exception(
                        f"Не удалось создать {i}: {resp.get(f'create_{i}')}"
                    )
            return created, to_create
        except Exception as e:
            logger.error(f"Ошибка создания батча: {e}")
            return created, []

    async def _delete_failed_appointments(self, ids: List[str]) -> None:
        cmd = {
            f"delete_{aid}": {
                "method": "crm.item.delete",
                "params": {
                    "id": aid,
                    "entityTypeId": constants.entityTypeId.appointment,
                },
            }
            for aid in ids
        }
        await bitrix.call_batch(cmd)

    async def run(self) -> Dict:
        """Главная точка: распределяем по дням и по расписанию специалистов."""
        logger.info("Запуск распределения занятий")
        await self.update_specialists_info()
        await self._update_specialists_schedules()

        user_id = self.data.user_id
        to_create = []
        failed = []

        # собираем все «аппойнтменты» в одном списке
        appointments = []
        for stage in self.data.data.values():
            for appoint in stage.data:
                for _ in range(appoint.quantity):
                    appointments.append(
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

        current_day = self.initial_time.date()
        last_day = current_day + timedelta(days=self.total_duration)
        remaining = appointments.copy()

        while remaining and current_day <= last_day:
            logger.info(f"Планирование на {current_day}")
            import random

            random.shuffle(remaining)

            # уже спланированные ребенку интервалы
            child_intervals = self._get_child_intervals(
                user_id,
                datetime.combine(current_day, datetime.min.time()).replace(
                    tzinfo=self.initial_time.tzinfo
                ),
            )

            day_changed = True
            while day_changed:
                day_changed = False
                for appt in remaining[:]:
                    tcode = appt["type_code"]
                    dur = appt["duration"]
                    candidates = appt["candidates"]
                    if not candidates:
                        failed.append({"type": tcode, "duration": dur})
                        remaining.remove(appt)
                        continue

                    placed = False
                    for spec in candidates:
                        for sid in list(spec.specialists_data.keys()):
                            fields = await self._try_place_in_schedule(
                                spec,
                                sid,
                                user_id,
                                tcode,
                                dur,
                                datetime.combine(
                                    current_day, datetime.min.time()
                                ).replace(tzinfo=self.initial_time.tzinfo),
                                child_intervals,
                            )
                            if fields:
                                to_create.append(fields)
                                remaining.remove(appt)
                                ns = datetime.fromisoformat(fields["ufCrm3StartDate"])
                                ne = datetime.fromisoformat(fields["ufCrm3EndDate"])
                                child_intervals.append((ns, ne))
                                child_intervals.sort(key=lambda x: x[0])
                                placed = True
                                day_changed = True
                                break
                        if placed:
                            break

                    if not placed:
                        logger.debug(f"Не влезло {tcode} в {current_day}")

                # если за проход ничего не влезло, выходим

            current_day += timedelta(days=1)

        if remaining:
            errmsg = "Не удалось запланировать:\n" + "\n".join(
                f"- {a['type_code']} ({a['duration']} мин)" for a in remaining
            )
            return {"error": errmsg}

        logger.info(f"Создаем {len(to_create)} в Битрикс")
        created_ids, payloads = await self._create_appointments_batch(to_create)
        if not created_ids:
            await self._delete_failed_appointments(created_ids)
            return {"error": "Ошибка при создании в Битрикс"}

        return {"appointments": payloads}
