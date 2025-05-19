
from fastapi import Body, FastAPI, Query
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
    await handler.update_specialists_schedules_test()    # Получили расписание и графики
    result = []
    for spec in handler.specialists:
        result.append({
            "code": spec.code,
            "possible_specs": spec.possible_specs,
            "specialists_data": getattr(spec, "specialists_data", {})
        })
    return result

@app.post('/most-free-specialist', tags=['Debug', 'Specialist'])
async def get_most_free_specialist(data: str = Query(...)):
    """
    Возвращает специалиста с максимальным количеством свободных окон, его расписание, свободные интервалы.
    """
    parsed_data = RequestShema.model_validate_json(data)
    handler = Handler(parsed_data)
    await handler.update_specialists_info()
    await handler.update_specialists_schedules()
    # Собираем всех специалистов со слотами
    spec_slots = [
        (spec, spec.get_free_slots_count())
        for spec in handler.specialists
    ]
    if not spec_slots:
        return {"error": "Нет специалистов"}
    # Выбираем самого свободного
    max_spec, max_count = max(spec_slots, key=lambda x: x[1])
    slots = max_spec.get_all_free_slots()
    result = {
        "code": max_spec.code,
        "max_free_slots": max_count,
        "free_slots": [
            {
                "specialist_id": spec_id,
                "start": slot.start.isoformat(),
                "end": slot.end.isoformat(),
                "duration_minutes": int((slot.end - slot.start).total_seconds() // 60)
            }
            for spec_id, slot in slots
        ],
        "specialists_data": getattr(max_spec, "specialists_data", {}),
    }
    return result

@app.post('/auto-assign', tags=['Автоматизация'])
async def auto_assign(data: str = Query(...)):
    parsed_data = RequestShema.model_validate_json(data)
    handler = Handler(parsed_data)
    return await handler.run()