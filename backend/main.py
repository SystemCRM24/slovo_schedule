import asyncio
import json
from fastapi import Body, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import BaseModel
from app.handler import Handler
from app.handler.handler_v2 import HandlerV2
from app.schemas import RequestSchema
from api.router import router as api_router
from app.utils import parse_query, parse_query_v2


# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(
    title="Слово - автоматизация заполнения расписания.",
    description="На основе данных сделки создает новый элемент смарт-процесса.",
)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/handle", status_code=200, tags=["Main"])
async def handle_appointments(data: str):
    parsed_data = parse_query(data)
    handler = Handler(parsed_data)
    return await handler.run()


async def handle_appointments_v2(data: dict):
    parsed_data = parse_query_v2(data)
    handler = HandlerV2(parsed_data)
    return await handler.run()


@app.post("/test-echo", tags=["Debug"])
async def test_echo(data: str = Query(...)):
    parsed = json.loads(data)
    return json.dumps(parsed, ensure_ascii=False)


class TestV2(BaseModel):
    deal_id: int = 202
    user_id: int = 1
    first_stage: dict = {"duration": 4, "data": [{"t": "R", "q": 2, "d": 30}]}
    second_stage: dict = {"duration": 4, "data": [{"t": "LM", "q": 3, "d": 15}]}


@app.post("/test-V2", status_code=200, tags=["test-v2"])
async def test_v2(data: TestV2 = Body(...)):
    return await handle_appointments_v2(data.dict())


@app.get("/test", status_code=200, tags=["Main"])
async def test():
    test_string = """{
        "deal_id":202, # ID сделки
        "user_id":1, # ID юзера 
        "first_stage": {"duration":4, # кол-во недель "data":[{"t":"R","q":2,"d":30}]}, ВАЛИДАЦИЯ # data "t" - type тип специалиста (может в нескольких подраздедениях) "q" - кол во занятий d - в минутах (не заполенено пропускаем) !!! КАК ТРАНЗАКЦИЯ !!! 
        "second_stage": {"duration":4, # кол-во недель "data":[{"t":"LM","q":3,"d":15}]} # максимум 2 занатия максимум 2 занаятия с одинаковым кодом R в день максимум 6 занятий  перерыв максимум 45 мин 
    }
    1 плучаем пулл спецалоисто 
    2 получаем их графиик и расписаение 
    3 распределяем по специалистам
    тестировать тестовая сделака с опрред id шником 202  
    """
    return await handle_appointments(test_string)


@app.post("/get-department-specialists", tags=["Debug", "Specialist"])
async def get_department_specialists(data: str = Query(...)):
    parsed_data = parse_query(data)
    handler = Handler(parsed_data)
    await handler.update_specialists_info_sd()
    result = []
    for spec in handler.specialists:
        result.append(
            {
                "code": spec.code,
                "quantity": spec.qty,
                "duration": spec.duration,
                "specialists": spec.possible_specs,
            }
        )
    return result


@app.post("/get-specialists-schedules", tags=["Debug", "Specialist"])
async def get_specialists_schedules(data: str = Query(...)):
    parsed_data = parse_query(data)
    handler = Handler(parsed_data)
    await handler.update_specialists_info()
    await handler.update_specialists_schedules_test()
    result = []
    for spec in handler.specialists:
        result.append(
            {
                "code": spec.code,
                "possible_specs": spec.possible_specs,
                "specialists_data": getattr(spec, "specialists_data", {}),
            }
        )
    return result


@app.post("/most-free-specialist", tags=["Debug", "Specialist"])
async def get_most_free_specialist(data: str = Query(...)):
    parsed_data = parse_query(data)
    handler = Handler(parsed_data)
    await handler.update_specialists_info_sd()
    await handler.update_specialists_schedules()
    spec_slots = [(spec, spec.get_free_slots_count()) for spec in handler.specialists]
    if not spec_slots:
        return {"error": "Нет специалистов"}
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
                "duration_minutes": int((slot.end - slot.start).total_seconds() // 60),
            }
            for spec_id, slot in slots
        ],
        "specialists_data": getattr(max_spec, "specialists_data", {}),
    }
    return result


@app.post("/auto-assign", tags=["Автоматизация"])
async def auto_assign(data: str = Query(...)):
    parsed_data = parse_query(data)
    handler = Handler(parsed_data)
    return await handler.run()
