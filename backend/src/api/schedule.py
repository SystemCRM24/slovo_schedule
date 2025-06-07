from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import HTTPException

from src.core import BXConstants, BitrixClient
from src.schemas.api import Schedule
from src.logger import logger


router = APIRouter(prefix="/schedule")


# @router.post("/", status_code=201, response_model=WorkScheduleCreateResponse)
# async def create_schedule(schedule: WorkScheduleCreate):
#     try:
#         fields = {
#             "ASSIGNED_BY_ID": schedule.specialist,
#             constants.uf.workSchedule.date: schedule.date,
#             constants.uf.workSchedule.intervals: schedule.intervals,
#         }
#         response = await BITRIX.call(
#             "crm.item.add",
#             {"entityTypeId": constants.entityTypeId.workSchedule, "fields": fields},
#         )
#         logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
#         if response.get("id"):
#             return WorkScheduleCreateResponse(id=response["id"])
#         else:
#             error = response.get("error", {})
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Ошибка Bitrix: {error.get('error_description', 'Неизвестная ошибка')}",
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", status_code=200)
async def get_schedule(id: int, bt: BackgroundTasks) -> Schedule:
    sety = BXConstants.schedule.entityTypeId
    data = await BitrixClient.get_crm_item(sety, id)
    if data is None:
        raise HTTPException(status_code=404, detail="Schedule id={id} not found")
    schedule = Schedule.from_bitrix(data)
    bt.add_task(logger.debug, f'Schedule id={id} was received.')
    return schedule


# @router.put("/", status_code=200)
# async def update_schedule(schedule: WorkScheduleCreate, id: int = Query(...)):
#     try:
#         fields = {
#             "ASSIGNED_BY_ID": schedule.specialist,
#             constants.uf.workSchedule.date: schedule.date,
#             constants.uf.workSchedule.intervals: schedule.intervals,
#         }
#         response = await BITRIX.call(
#             "crm.item.update",
#             {
#                 "entityTypeId": constants.entityTypeId.workSchedule,
#                 "id": id,
#                 "fields": fields,
#             },
#         )
#         logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
#         if response.get("id", None) == id:
#             return True
#         else:
#             error = response.get("error", {})
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Ошибка Bitrix: {error.get('error_description', 'Неизвестная ошибка')}",
#             )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}", status_code=204)
async def delete_schedule(id: int, bt: BackgroundTasks):
    sety = BXConstants.schedule.entityTypeId
    result = await BitrixClient.delete_crm_item(sety, id)
    if not result:
        raise HTTPException(404, f'Schedule id={id} not found.')
    bt.add_task(logger.debug, f'Schedule id={id} was deleted.')
