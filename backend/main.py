from fastapi import FastAPI

from app.main import Handler


app = FastAPI(
    title='Слово - автоматизация заполнения расписания.',
    description="На основе данных сделки создает новый элемент смарт-процесса."
)


@app.post('/handle', status_code=200, tags=['Main'])
async def handle_appointment(deal_id: str, user_id: str = None):
    handler = Handler(deal_id, user_id)
    return await handler.run()
