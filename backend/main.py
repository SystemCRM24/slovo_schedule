from fastapi import Body, FastAPI, Query

from app.handler import Handler
from app.schemas import RequestShema


app = FastAPI(
    title='Слово - автоматизация заполнения расписания.',
    description="На основе данных сделки создает новый элемент смарт-процесса."
)

"""
{"deal_id":202,"user_id":1,"data":[{"t":"R","q":2,"d":30},{"t":"LM","q":3,"d":15}]}
"""


@app.post('/handle', status_code=200, tags=['Main'])
async def handle_appointments(data: str):
    parsed_data = RequestShema.model_validate_json(data)
    handler = Handler(parsed_data)
    return await handler.run()


@app.get('/test', status_code=200)
async def test():
    """
    Тестовый метод, для вызова основного со со следующим параметром\n
    {"deal_id":202,"user_id":1,"data":[{"t":"R","q":2,"d":30},{"t":"LM","q":3,"d":15}]}
    """
    test_string = '{"deal_id":202,"user_id":1,"data":[{"t":"R","q":2,"d":30},{"t":"LM","q":3,"d":15}]}'
    return await handle_appointments(test_string)

@app.post('/get-department-specialists', tags=['Debug', 'Specialist'])
async def get_department_specialists(data: str = Query(...)):
    """
    Получить список всех специалистов по департаменту
    """
    parsed_data = RequestShema.model_validate_json(data)
    handler = Handler(parsed_data)
    await handler.update_specialists_info_sd()
    result = []
    for spec in handler.specialists:
        result.append({
            "code": spec.code,
            "quantity": spec.qty,
            "duration": spec.duration,
            "specialists": spec.possible_specs
        })
    return result

@app.post('/get-specialists-schedules', tags=['Debug', 'Specialist'])
async def get_specialists_schedules(data: str = Query(...)):
    """
    Получить расписание и графики по всем специалистам по входным данным
    """
    parsed_data = RequestShema.model_validate_json(data)
    handler = Handler(parsed_data)
    await handler.update_specialists_info()         # Получили специалистов
    await handler.update_specialists_schedules()    # Получили расписание и графики
    result = []
    for spec in handler.specialists:
        result.append({
            "code": spec.code,
            "possible_specs": spec.possible_specs,
            "specialists_data": getattr(spec, "specialists_data", {})
        })
    return result