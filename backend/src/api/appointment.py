from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import HTTPException

from src.core import BitrixClient, BXConstants
from src.schemas.api import Appointment
from src.logger import logger


router = APIRouter(prefix="/appointment")


# @router.post("/", status_code=201, response_model=AppointmentCreateResponse)
# async def create_appointment(appointment: AppointmentCreate):
#     try:
#         fields = {
#             "ASSIGNED_BY_ID": appointment.specialist,
#             constants.uf.appointment.patient: appointment.patient,
#             constants.uf.appointment.start: appointment.start,
#             constants.uf.appointment.end: appointment.end,
#             constants.uf.appointment.code: constants.listFieldValues.appointment.idByCode[
#                 appointment.code
#             ],
#         }
#         response = await BITRIX.call(
#             "crm.item.add",
#             {"entityTypeId": constants.entityTypeId.appointment, "fields": fields},
#         )
#         logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
#         if response.get("id"):
#             return AppointmentCreateResponse(
#                 id=response["id"],
#             )
#         else:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Ошибка Bitrix: {response.get('error', 'Неизвестная ошибка')}",
#             )
#     except KeyError as e:
#         raise HTTPException(status_code=400, detail=f"Недопустимый статус или код: {e}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", status_code=200)
async def get_appointment(id: int) -> Appointment:
    aety = BXConstants.appointment.entityTypeId
    data = await BitrixClient.get_crm_item(aety, id)
    raise HTTPException(status_code=404, detail=f"Appointment id={id} not found")
    if data is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return Appointment.from_bx(data)


# @router.put("/", status_code=200)
# async def update_appointment(appointment: AppointmentCreate, id: int = Query(...)):
#     try:
#         fields = {
#             "ASSIGNED_BY_ID": appointment.specialist,
#             constants.uf.appointment.patient: appointment.patient,
#             constants.uf.appointment.start: appointment.start,
#             constants.uf.appointment.end: appointment.end,
#             constants.uf.appointment.code: constants.listFieldValues.appointment.idByCode[
#                 appointment.code
#             ],
#         }
#         response = await BITRIX.call(
#             "crm.item.update",
#             {
#                 "entityTypeId": constants.entityTypeId.appointment,
#                 "id": id,
#                 "fields": fields,
#             },
#         )
#         logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
#         if response.get("id"):
#             return Appointment.from_bitrix(response)
#         else:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Ошибка Bitrix: {response.get('error', 'Неизвестная ошибка')}",
#             )
#     except KeyError as e:
#         raise HTTPException(status_code=400, detail=f"Недопустимый статус или код: {e}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}", status_code=204)
async def delete_appointment(id: int, bt: BackgroundTasks):
    """Удаляет элемент смарт процесса расписание."""
    aety = BXConstants.appointment.entityTypeId
    result = await BitrixClient.delete_crm_item(aety, id)
    if result:
        bt.add(logger.debug(f'Appointment id={id} was deleted.'))
        return
    raise HTTPException(404, f'Appointment id={id} not found.')
