from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.handler import Handler
from app.schemas import RequestShema

from api.router import router as api_router


app = FastAPI(
    title='Слово - автоматизация заполнения расписания.',
    description="На основе данных сделки создает новый элемент смарт-процесса."
)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/handle', status_code=200, tags=['Main'])
async def handle_appointments(data: str):
    parsed_data = RequestShema.model_validate_json(data)
    handler = Handler(parsed_data)
    return await handler.run()


@app.get('/test', status_code=200, tags=['Main'])
async def test():
    """
    Тестовый метод, для вызова основного со со следующим параметром\n
    {"deal_id":202,"user_id":1,"data":[{"t":"R","q":2,"d":30},{"t":"LM","q":3,"d":15}]}
    """
    test_string = '{"deal_id":202,"user_id":1,"data":[{"t":"R","q":2,"d":30},{"t":"LM","q":3,"d":15}]}'
    return await handle_appointments(test_string)
