import asyncio

from src.core import BXConstants, BitrixClient
from src.logger import logger


async def on_startup():
    """Закидывает корутины в фон, которые нужно выполнить при старте приложения"""
    logger.warning('Updating Bitrix constants.')
    await asyncio.gather(
        update_constants()
    )


async def update_constants():
    """Обновляет константные значения"""
    data = await BitrixClient.get_crm_item_fields(BXConstants.appointment.entityTypeId)
    codes = data.get(BXConstants.appointment.uf.code)
    codes_items = codes.get('items')
    for item in codes_items:
        id = item['ID']
        code = item['VALUE']
        BXConstants.appointment.lfv.idByCode[code] = id
        BXConstants.appointment.lfv.codeById[id] = code
    statuses = data.get(BXConstants.appointment.uf.status)
    status_items = statuses.get('items')
    for item in status_items:
        id, status = int(item['ID']), item['VALUE']
        BXConstants.appointment.lfv.idByStatus[status] = id
        BXConstants.appointment.lfv.statusById[id]= status
