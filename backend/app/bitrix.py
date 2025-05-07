from fast_bitrix24 import BitrixAsync

from .settings import settings


BITRIX = BitrixAsync(settings.BITRIX_WEBHOOK)


async def get_deal_info(deal_id: str) -> dict:
    """Получает информацию о сделке"""
    response: dict = await BITRIX.call('crm.deal.get', {'id': deal_id}, raw=True)
    return response.get('result', {})
