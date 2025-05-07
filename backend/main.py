from fastapi import FastAPI

from app.bitrix import get_deal_info


app = FastAPI(
    title='Слово - автоматизация заполнения расписания.',
    description="На основе данных сделки создает новый элемент смарт-процесса."
)


@app.post('/handle', status_code=200, tags=['Main'])
async def handle_appointment(deal_id: str, user_id: str = None):
    deal = await get_deal_info(deal_id)
    return deal
