from datetime import datetime, timedelta

from app.settings import Settings
from app.schemas import RequestSchema
from app import bitrix
from app.bitrix import BITRIX
from app.utils import BatchBuilder

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
                    chosen = max(candidates, key=lambda s: s.get_free_slots_count(), default=None)
                    if not chosen or chosen.get_free_slots_count() == 0:
                        continue

                    free_slots = chosen.get_all_free_slots()
                    slot_found = False
                    for spec_id, slot in free_slots:
                        if slot.duration().total_seconds() < duration * 60:
                            continue

                        data = chosen.specialists_data[spec_id]
                        appointments = data.get('appointments', [])

                        slot_date = slot.start.date()
                        appoints_same_day = [
                            a for a in appointments
                            if 'ufCrm3StartDate' in a and
                            datetime.fromisoformat(a['ufCrm3StartDate']).date() == slot_date
                        ]
                        if len(appoints_same_day) >= 6:
                            continue
                        child_same_day = [
                            a for a in appoints_same_day
                            if a.get('user_id') == user_id
                        ]
                        if len(child_same_day) >= 2:
                            continue

                        new_start = slot.start
                        new_end = new_start + timedelta(minutes=duration)

                        ok = True
                        for a in appoints_same_day:
                            exist_start = datetime.fromisoformat(a['ufCrm3StartDate'])
                            exist_end = datetime.fromisoformat(a['ufCrm3EndDate'])
                            if not (new_end <= exist_start or new_start >= exist_end):
                                ok = False
                                break
                            gap1 = abs((exist_start - new_end).total_seconds()) // 60
                            gap2 = abs((new_start - exist_end).total_seconds()) // 60
                            if (0 < gap1 < 15) or (0 < gap2 < 15):
                                ok = False
                                break
                            if (gap1 > 0 and gap1 > 45) or (gap2 > 0 and gap2 > 45):
                                ok = False
                                break
                        if not ok:
                            continue

                        new_appt = {
                            "specialist_id": spec_id,
                            "specialist_type": type_code,
                            "user_id": user_id,
                            "start": new_start.isoformat(),
                            "end": new_end.isoformat()
                        }

                        appointments.append({
                            "ufCrm3StartDate": new_start.isoformat(),
                            "ufCrm3EndDate": new_end.isoformat(),
                            "user_id": user_id
                        })
                        appointments_to_create.append(new_appt)

                        await self.create_schedule_entry(new_appt)
                        slot_found = True
                        break

                    if not slot_found:
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

            print(f"Для специалиста {spec.code} найдено {len(users)} специалистов")
    
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

    async def create_schedule_entry(self, appointment: dict):
        entityTypeId = 1036
        fields = {
            "assignedById": int(appointment["specialist_id"]),
            "ufCrm3StartDate": appointment["start"],
            "ufCrm3EndDate": appointment["end"],
            "ufCrm3ParentDeal": self.data.deal_id,
            "ufCrm3Child": appointment.get("user_id"),
            "user_id": appointment["user_id"],
            "ufCrm3Type": appointment["specialist_type"],
        }
        # Здесь предполагается, что у тебя есть объект bitrix для запросов к Bitrix24
        response = await BITRIX.call("crm.item.add", {
            "entityTypeId": entityTypeId,
            "fields": fields
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
