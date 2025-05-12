from fastapi import FastAPI

from app.handler import Handler
from app.schemas import RequestShema


app = FastAPI(
    title='Слово - автоматизация заполнения расписания.',
    description="На основе данных сделки создает новый элемент смарт-процесса."
)

"""
"{"deal_id":202,"user_id":1,"data":[{"t":"R","q":2,"d":30},{"t":"LM","q":3,"d":15}]}"
"""


@app.post('/handle', status_code=200, tags=['Main'])
async def handle_appointment(data: str):
    parsed_data = RequestShema.model_validate_json(data)
    handler = Handler(parsed_data)
    return await handler.run()
