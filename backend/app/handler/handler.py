from datetime import datetime, timedelta

from app.settings import Settings
from app.schemas import RequestSchema
from app import bitrix
from app.bitrix import BITRIX
from app.utils import BatchBuilder
from api.constants import constants

from .specialist import Specialist


class Handler:
    def __init__(self, data: RequestSchema):
        self.initial_time = datetime.now(Settings.TIMEZONE)
        self.data = data
        self.specialists = self.create_specialists()
    
    def create_specialists(self) -> tuple:
        specialists = []
        for stage in self.data.data.values():
            for d in stage.data:
                specialists.append(Specialist(self.initial_time, d.type, d.quantity, d.duration))
        return tuple(specialists)
    
    @staticmethod
    def get_appointments_on_day(appointments, user_id, dt):
        target_day = dt.date()
        return [
            a for a in appointments
            if a.get("user_id") == user_id and
            datetime.fromisoformat(a['ufCrm3StartDate']).date() == target_day
        ]

    @staticmethod
    def get_specialist_appointments_on_day(appointments, dt):
        target_day = dt.date()
        return [
            a for a in appointments
            if datetime.fromisoformat(a['ufCrm3StartDate']).date() == target_day
        ]
    
    def is_slot_ok(self, new_start, new_end, appointments, min_break=15):
        print(f"\n[is_slot_ok] Проверка для {new_start} — {new_end} appointments={appointments}")
        for a in appointments:
            exist_start = datetime.fromisoformat(a['ufCrm3StartDate'])
            exist_end = datetime.fromisoformat(a['ufCrm3EndDate'])
            # Проверка на пересечение интервалов
            if not (new_end <= exist_start or new_start >= exist_end):
                return False
            # Проверка на минимальный разрыв
            gap_before = (new_start - exist_end).total_seconds() / 60
            gap_after = (exist_start - new_end).total_seconds() / 60
            if 0 <= gap_before < min_break:
                return False
            if 0 <= gap_after < min_break:
                return False
        print("  OK!")
        return True

    async def assign_appointment(self, chosen, user_id, appoint, type_code, duration):
        """
        Пытается назначить appointment для выбранного специалиста chosen.
        Возвращает fields, если получилось назначить, иначе None.
        """
        for spec_id, slot in chosen.get_all_free_slots():
            # Проверяем, подходит ли длительность слота
            if slot.duration().total_seconds() < duration * 60:
                continue

            data = chosen.specialists_data[spec_id]
            appointments = data.setdefault('appointments', [])

            new_start = slot.start
            new_end = new_start + timedelta(minutes=duration)

            # --- ОГРАНИЧЕНИЕ: не больше 2 занятий у ребёнка в день ---
            child_appointments_today = self.get_appointments_on_day(appointments, user_id, new_start)
            if len(child_appointments_today) >= 2:
                print("  Уже 2 занятия у ребёнка в этот день!")
                continue

            # --- ОГРАНИЧЕНИЕ: не больше 6 занятий у специалиста в день ---
            spec_appointments_today = self.get_specialist_appointments_on_day(appointments, new_start)
            if len(spec_appointments_today) >= 6:
                print("  Уже 6 занятий у специалиста в этот день!")
                continue

            # Главная проверка на пересечения и перерывы
            if not self.is_slot_ok(new_start, new_end, appointments):
                continue

            # Формируем fields для Bitrix и т.д.
            fields = {
                "assignedById": int(spec_id),
                "ufCrm3StartDate": new_start.isoformat(),
                "ufCrm3EndDate": new_end.isoformat(),
                "ufCrm3ParentDeal": self.data.deal_id,
                "ufCrm3Child": user_id,
                "user_id": user_id,
                "ufCrm3Type": appoint.t if hasattr(appoint, "t") else type_code,
                "ufCrm3Code": type_code
            }

            # Создаём запись в Bitrix
            await self.create_schedule_entry(fields)

            # Обновляем appointments для этого специалиста (добавляем занятие!)
            appointments.append({
                "ufCrm3StartDate": new_start.isoformat(),
                "ufCrm3EndDate": new_end.isoformat(),
                "user_id": user_id,
                "ufCrm3Type": type_code,
                "ufCrm3Code": getattr(appoint, 'code', "unknown")
            })
            chosen.specialists_data[spec_id]['appointments'] = appointments

            return fields  # Возвращаем созданную запись

        # Если ни один слот не подошёл
        return None

    async def run(self) -> dict:
        await self.update_specialists_info()
        await self.update_specialists_schedules()

        user_id = self.data.user_id
        appointments_to_create = []

        for stage in self.data.data.values():
            for appoint in stage.data:
                type_code = appoint.type
                quantity = appoint.quantity
                duration = appoint.duration

                candidates = [spec for spec in self.specialists if spec.code == type_code]
                if not candidates:
                    continue

            for _ in range(quantity):
                # САМЫЙ КРИТИЧНЫЙ МОМЕНТ — пересчитывать на каждом шаге!
                chosen = max(
                    candidates, 
                    key=lambda s: s.get_free_slots_count(), 
                    default=None
                )
                if not chosen or chosen.get_free_slots_count() == 0:
                    continue

                # ПЕРЕСЧЁТ! get_all_free_slots на каждой итерации!
                fields = await self.assign_appointment(
                    chosen, user_id, appoint, type_code, duration
                )
                if fields:
                    appointments_to_create.append(fields)
                else:
                    continue

        return {"appointments": appointments_to_create}

    
    async def update_specialists_info(self):
        """Обновляет инфу для возможных специалистов"""
        departments = await bitrix.get_all_departments()
        batches = tuple(s.get_specialists_info_batch(departments) for s in self.specialists)
        cmd = {index: value for index, value in enumerate(batches)}
        response = await bitrix.call_batch(cmd)
        for index, specs in enumerate(self.specialists):
            specs.possible_specs = response[index]

    async def update_specialists_info_sd(self):
        """
        Обновляет инфу о возможных специалистах для каждого Specialist в self.specialists.
        Находит id подразделения по коду, делает батч-запросы, кладёт результат в spec.possible_specs.
        """
        departments = await bitrix.get_all_departments()

        # Для каждого специалиста находим id подразделения по коду (t)
        code_to_department_id = {}
        for dep_id, dep in departments.items():
            code_to_department_id[dep['NAME']] = dep_id

        batch_cmd = {}
        for i, spec in enumerate(self.specialists):
            department_id = code_to_department_id.get(spec.code)
            if not department_id:
                print(f'Подразделение {spec.code} не найдено в Bitrix!')
                continue
            params = {
                'filter': {
                    'ACTIVE': True,
                    'UF_DEPARTMENT': department_id
                }
            }
            batch_cmd[i] = BatchBuilder('user.get', params).build()
        
        if not batch_cmd:
            return None

        response = await bitrix.call_batch(batch_cmd)

        # Сопоставляем специалистов
        for i, spec in enumerate(self.specialists):
            result = response.get(str(i), []) if isinstance(response, dict) else response[i]
            users = result.get('result', result) if isinstance(result, dict) else result
            spec.possible_specs = users

            print(f"Для специалиста {spec.code} найдено {len(users)} юзеров")
    
    async def update_specialists_schedules(self):
        """Получает график и расписание занятий для всех специалистов."""
        cmd = {}
        date_start = self.initial_time.replace(hour=0, minute=0, second=0, microsecond=0)
        date_start_iso = date_start.isoformat()

        batch_index = 0
        mapping = {}  # Связь: batch_index = (Specialist, specialist_id)

        for spec in self.specialists:
            for possible_spec in spec.possible_specs:
                specialist_id = possible_spec.get('ID')
                if not specialist_id:
                    continue

                # Получить график (1042)
                cmd[batch_index] = BatchBuilder('crm.item.list', {
                    'entityTypeId': 1042,
                    'filter': {
                        '>=ufCrm4Date': date_start_iso,
                        'assignedById': specialist_id
                    },
                    'order': {'ufCrm4Date': 'ASC'}
                }).build()
                mapping[batch_index] = (spec, specialist_id, 'schedule')
                batch_index += 1

                # Получить расписание занятий (1036)
                cmd[batch_index] = BatchBuilder('crm.item.list', {
                    'entityTypeId': 1036,
                    'filter': {
                        '>=ufCrm3StartDate': date_start_iso,
                        'assignedById': specialist_id
                    },
                    'order': {'ufCrm3StartDate': 'ASC'}
                }).build()
                mapping[batch_index] = (spec, specialist_id, 'appointments')
                batch_index += 1

        response = await bitrix.call_batch(cmd)
        
        for idx, (spec, specialist_id, typ) in mapping.items():
            result = response[idx]  # Это dict, а не list (очень важно!!!)
            # result = {'result': {'items': [...]}} или просто {'items': [...]}
            items = result.get('result', {}).get('items', result.get('items', []))
            if not hasattr(spec, 'specialists_data'):
                spec.specialists_data = {}
            if specialist_id not in spec.specialists_data:
                spec.specialists_data[specialist_id] = {'schedule': [], 'appointments': []}
            spec.specialists_data[specialist_id][typ] = items

    async def update_specialists_schedules_test(self):
        """Получает график и расписание занятий для всех специалистов."""
        cmd = {}
        # Вставляем позавчерашнюю дату
        from datetime import datetime, timedelta
        pozavchera = datetime.now() - timedelta(days=5)
        date_start = pozavchera.replace(hour=0, minute=0, second=0, microsecond=0)
        date_start_iso = date_start.isoformat()

        batch_index = 0
        mapping = {}  # Связь: batch_index = (Specialist, specialist_id)

        for spec in self.specialists:
            for possible_spec in spec.possible_specs:
                specialist_id = possible_spec.get('ID')
                if not specialist_id:
                    continue

                # Получить график (1042)
                cmd[batch_index] = BatchBuilder('crm.item.list', {
                    'entityTypeId': 1042,
                    'filter': {
                        '>=ufCrm4Date': date_start_iso,
                        'assignedById': specialist_id
                    },
                    'order': {'ufCrm4Date': 'ASC'}
                }).build()
                mapping[batch_index] = (spec, specialist_id, 'schedule')
                batch_index += 1

                # Получить расписание занятий (1036)
                cmd[batch_index] = BatchBuilder('crm.item.list', {
                    'entityTypeId': 1036,
                    'filter': {
                        '>=ufCrm3StartDate': date_start_iso,
                        'assignedById': specialist_id
                    },
                    'order': {'ufCrm3StartDate': 'ASC'}
                }).build()
                mapping[batch_index] = (spec, specialist_id, 'appointments')
                batch_index += 1

        response = await bitrix.call_batch(cmd)
        
        for idx, (spec, specialist_id, typ) in mapping.items():
            result = response[idx]  # Это dict, а не list (очень важно!!!)
            # result = {'result': {'items': [...]}} или просто {'items': [...]}
            items = result.get('result', {}).get('items', result.get('items', []))
            if not hasattr(spec, 'specialists_data'):
                spec.specialists_data = {}
            if specialist_id not in spec.specialists_data:
                spec.specialists_data[specialist_id] = {'schedule': [], 'appointments': []}
            spec.specialists_data[specialist_id][typ] = items
    
    async def create_schedule_entry(self, fields: dict, specialist=None):
        entityTypeId = constants.entityTypeId.appointment

        code = (
            fields.get("ufCrm3Code")
            or fields.get("code")
            or (specialist.code if specialist and hasattr(specialist, "code") else None)
        )
        code_id = constants.listFieldValues.appointment.idByCode.get(code, str(code))

        # Статус "Забронировано" — это всегда 50
        status_id = 50

        response = await BITRIX.call("crm.item.add", {
            "entityTypeId": entityTypeId,
            "fields": {
                "ASSIGNED_BY_ID": str(fields.get("assignedById") or fields.get("specialist_id") or fields.get("spec_id")),
                "ufCrm3StartDate": str(fields.get("ufCrm3StartDate") or fields.get("start") or fields.get("start_date")),
                "ufCrm3EndDate": str(fields.get("ufCrm3EndDate") or fields.get("end") or fields.get("end_date")),
                "ufCrm3ParentDeal": str(fields.get("ufCrm3ParentDeal") or fields.get("deal_id")),
                "ufCrm3Children": str(fields.get("ufCrm3Children") or fields.get("user_id")),
                "user_id": str(fields.get("user_id")),
                "ufCrm3Type": str(fields.get("ufCrm3Type") or fields.get("type_code") or fields.get("specialist_type") or fields.get("t")),
                "ufCrm3Status": str(status_id),
                "ufCrm3Code": str(code_id),
            }
        })
        return response
    # async def get_listfield_values(self) -> dict:
    #     """Возвращает словарь, где ключи - id полей, а значения - значения"""
    #     fields = await bitrix.get_deal_field_values()
    #     codes = fields.get(UserFields.code, {}).get('items', [])
    #     return {c.get('ID', None): c.get('VALUE', None) for c in codes}

    # async def get_specs_schedules(self, specs: list, duration: int | None) -> list[Specialist]:
    #     """Получает рабочие графики и расписания приемов специалистов"""
    #     cmd = {}
    #     date_start = self.initial_time.replace(hour=0, minute=0, second=0, microsecond=0)
    #     date_start_iso = date_start.isoformat()
    #     for index, specialist in enumerate(specs):
    #         index *= 2
    #         spec_id = specialist.get('ID', '0')
    #         batch = BatchBuilder('crm.item.list')
    #         batch.params = {
    #             'entityTypeId': 1042,       # для получения графика работы специалиста
    #             'filter': {
    #                 '>=ufCrm4Date': date_start_iso,
    #                 'assignedById': spec_id
    #             },
    #             'order': {'ufCrm4Date': 'ASC'}
    #         }
    #         cmd[index] = batch.build()
    #         batch.params = {
    #             'entityTypeId': 1036,       # Для получения расписания занятий
    #             'filter': {
    #                 '>=ufCrm3StartDate': date_start_iso,
    #                 'assignedById': spec_id                    
    #             },
    #             'order': {'ufCrm3StartDate': 'ASC'}
    #         }
    #         cmd[index + 1] = batch.build()
    #     response: list = await bitrix.call_batch(cmd)
    #     result = []
    #     for i in range(0, len(response), 2):
    #         specialist = specs[i // 2]
    #         spec_id = specialist.get('ID', '0')
    #         result.append(Specialist(
    #             spec_id,
    #             schedule=response[i]['items'],
    #             appointments=response[i+1]['items'],
    #             duration=duration,
    #             now=self.initial_time
    #         ))
    #     return result

    # @staticmethod
    # def get_appointment_duration(deal: dict) -> int | None:
    #     """Получает из сделки продолжительность приема"""
    #     duration = deal.get('UF_CRM_1746625717138', '')
    #     try:
    #         return int(duration)
    #     except:
    #         return None

    # async def create_appointment(self, deal: dict, schedule: Specialist):
    #     """Создает занятие"""
    #     result = await bitrix.create_appointment({
    #         'ASSIGNED_BY_ID': schedule.specialist_id,
    #         'ufCrm3Children': 170,
    #         'ufCrm3StartDate': schedule.last_find.start.isoformat(),
    #         'ufCrm3EndDate': schedule.last_find.end.isoformat(),
    #         'ufCrm3Code': '55',
    #         'ufCrm3Status': 50
    #     })
    #     return result.get('item', None)
