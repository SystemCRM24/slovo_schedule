import asyncio
import json
from typing import List
from fastapi import Body, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.handler import Handler
from app.handler.handler_v2 import HandlerV2
from app.schemas import RequestSchema
from api.router import router as api_router
from app.utils import parse_query, parse_query_v2


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
    # parsed_data = parse_query(data)
    # handler = Handler(parsed_data)
    return await handle_appointments_v2(data)


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

class AppointmentResponse(BaseModel):
    assignedById: int
    ufCrm3StartDate: str
    ufCrm3EndDate: str
    ufCrm3ParentDeal: int
    ufCrm3Children: int
    user_id: int
    ufCrm3Type: str
    ufCrm3Code: str
    id: int

class SuccessResponse(BaseModel):
    appointments: List[AppointmentResponse]

class ErrorResponse(BaseModel):
    detail: str
    error_code: int

@app.post("/create-shedule-batch", 
          status_code=200, 
          tags=["test-v2"],
          summary="Создание расписания занятий",
          response_description="Результат создания расписания",
          responses={
              200: {
                  "description": "Расписание успешно создано",
                  "content": {
                      "application/json": {
                          "example": {
                              "appointments": [
                                  {
                                      "assignedById": 12,
                                      "ufCrm3StartDate": "2025-06-03T09:00:00+03:00",
                                      "ufCrm3EndDate": "2025-06-03T09:30:00+03:00",
                                      "ufCrm3ParentDeal": 202,
                                      "ufCrm3Children": 158,
                                      "user_id": 1,
                                      "ufCrm3Type": "R",
                                      "ufCrm3Code": "R",
                                      "id": 312
                                  }
                              ]
                          }
                      }
                  },
                  "model": SuccessResponse
              },
              400: {
                  "description": "Некорректные входные данные",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": "Invalid input data",
                              "error_code": 400
                          }
                      }
                  },
                  "model": ErrorResponse
              },
              404: {
                  "description": "Сделка или пользователь не найдены",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": "Deal not found",
                              "error_code": 404
                          }
                      }
                  },
                  "model": ErrorResponse
              },
              500: {
                  "description": "Ошибка сервера при обработке запроса",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": "Internal server error",
                              "error_code": 500
                          }
                      }
                  },
                  "model": ErrorResponse
              }
          })
async def test_v2(data: TestV2 = Body(..., example={
    "deal_id": 202,
    "user_id": 1,
    "first_stage": {
        "duration": 4,
        "data": [{
            "t": "R",
            "q": 2,
            "d": 30
        }]
    },
    "second_stage": {
        "duration": 4,
        "data": [{
            "t": "LM",
            "q": 3,
            "d": 15
        }]
    }
})):
    """
    API для формирования расписания занятий по двум этапам.

    ### Описание параметров:
    - **deal_id**: ID сделки в CRM (обязательный)
    - **user_id**: ID пользователя (обязательный)
    
    ### Параметры first_stage (первый этап):
    - **duration**: Длительность этапа в неделях
    - **data**: Список типов занятий:
        - **t**: Тип специалиста (код)
        - **q**: Количество занятий в неделю
        - **d**: Длительность занятия в минутах

    ### Параметры second_stage (второй этап):
    - **duration**: Длительность этапа в неделях
    - **data**: Список типов занятий:
        - **t**: Тип специалиста (код)
        - **q**: Количество занятий в неделю
        - **d**: Длительность занятия в минутах
    """
    return await handle_appointments_v2(data.dict())

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
