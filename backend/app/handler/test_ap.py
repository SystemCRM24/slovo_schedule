import logging
from fast_bitrix24 import BitrixAsync
from typing import List, Dict, Any
import asyncio


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BITRIX = BitrixAsync(
    "https://bx24.neuroslovo.ru/rest/1/8s38ofulujczao7p/", verbose=True
)


async def check_fields(bitrix: BitrixAsync, entity_type_id: int = 1036) -> List[str]:
    """Проверяет доступные поля для entityTypeId."""
    try:
        response = await bitrix.get_all(
            "crm.item.fields", {"entityTypeId": entity_type_id}
        )
        fields = response.get("fields", {})
        available_fields = list(fields.keys())
        logger.info(f"Доступные поля: {available_fields}")
        return available_fields
    except Exception as e:
        logger.error(f"Ошибка при получении полей: {e}")
        return []


async def fetch_appointments(
    bitrix: BitrixAsync, parent_deal_id: int = 202, appointment_ids: List[int] = None
) -> List[Dict[str, Any]]:
    """
    Извлекает занятия из Bitrix по ID или фильтрам.
    """
    try:
        entity_type_id = 1036
        available_fields = await check_fields(bitrix, entity_type_id)
        items = []

        select_fields = [
            "id",
            "assignedById",
            "ufCrm3StartDate",
            "ufCrm3EndDate",
            "ufCrm3Type",
            "ufCrm3Code",
        ]
        if "ufCrm3Child" in available_fields:
            select_fields.append("ufCrm3Child")
        if "ufCrm3ParentDeal" in available_fields:
            select_fields.append("ufCrm3ParentDeal")

        if appointment_ids:
            cmd = {
                f"item_{id}": {
                    "method": "crm.item.get",
                    "params": {"entityTypeId": entity_type_id, "id": id},
                }
                for id in appointment_ids
            }
            response = await bitrix.call_batch(cmd)
            logger.debug(f"Ответ API для ID {appointment_ids}: {response}")

            items = []
            for id in appointment_ids:
                key = f"item_{id}"
                if (
                    key in response.get("result", {})
                    and "result" in response["result"][key]
                ):
                    item = response["result"][key]["result"].get("item")
                    if item:
                        items.append(item)
                    else:
                        logger.warning(f"Запись с ID {id} не найдена")
                else:
                    logger.warning(f"Ответ для ID {id} пустой или содержит ошибку")

        else:
            filter_params = {
                "entityTypeId": entity_type_id,
                "filter": {
                    ">=ufCrm3StartDate": "2025-05-29T00:00:00+03:00",
                    "<=ufCrm3StartDate": "2025-05-31T23:59:59+03:00",
                    "assignedById": ["12", "19"],
                },
                "select": select_fields,
            }
            if "ufCrm3Child" in available_fields:
                filter_params["filter"]["ufCrm3Child"] = "1"
            if "ufCrm3ParentDeal" in available_fields:
                filter_params["filter"]["ufCrm3ParentDeal"] = str(parent_deal_id)

            response = await bitrix.get_all("crm.item.list", filter_params)
            logger.debug(f"Ответ API для фильтрации: {response}")
            items = response

        code_map = {
            "52": "L",
            "54": "LM",
            "55": "D1-3,5",
            "56": "D 3,5+",
            "57": "R",
            "58": "Z",
            "59": "A",
            "60": "NT",
            "61": "НДГ",
            "62": "NP",
            "63": "P",
            "64": "СИ",
            "65": "КИТ",
            "66": "АВА-Р",
            "67": "i",
            "68": "К",
            "69": "d",
            "70": "КК",
            "71": "d-ава",
            "72": "dNP",
            "73": "dd",
            "74": "dL",
            "75": "dP",
        }

        appointments = []
        for item in items:
            try:
                code = item.get("ufCrm3Code", [])
                appointment = {
                    "id": int(item["id"]),
                    "assignedById": int(item.get("assignedById", 0)),
                    "ufCrm3StartDate": item.get("ufCrm3StartDate"),
                    "ufCrm3EndDate": item.get("ufCrm3EndDate"),
                    "ufCrm3Type": item.get("ufCrm3Type"),
                    "ufCrm3Code": (
                        code_map.get(code[0], code[0]) if code and len(code) else None
                    ),
                    "ufCrm3Child": item.get("ufCrm3Child"),
                    "ufCrm3ParentDeal": item.get("ufCrm3ParentDeal"),
                }
                appointments.append(appointment)
            except Exception as e:
                logger.error(f"Ошибка при обработке записи {item.get('id')}: {e}")

        logger.info(
            f"Извлечено {len(appointments)} занятий: {[appt['id'] for appt in appointments]}"
        )
        return appointments
    except Exception as e:
        logger.error(f"Ошибка при извлечении занятий: {e}")
        return []


async def main():
    appointments = await fetch_appointments(
        BITRIX, appointment_ids=[210, 211, 212, 213, 214]
    )
    print("Appointments by ID:", appointments)

    appointments_by_filter = await fetch_appointments(BITRIX, parent_deal_id=202)
    print("Appointments by filter:", appointments_by_filter)


if __name__ == "__main__":
    asyncio.run(main())
