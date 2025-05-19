from fastapi import APIRouter, HTTPException, Query
from .models.appointment_models import (
    Appointment,
    AppointmentCreate,
    AppointmentCreateResponse,
)
from app.bitrix import BITRIX
from .constants import constants
import logging

logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix="/appointment", tags=["Appointment"])


@router.post("/", status_code=201, response_model=AppointmentCreateResponse)
async def create_appointment(appointment: AppointmentCreate):
    try:
        fields = {
            "ASSIGNED_BY_ID": appointment.specialist,
            constants.uf.appointment.patient: appointment.patient,
            constants.uf.appointment.start: appointment.start,
            constants.uf.appointment.end: appointment.end,
            constants.uf.appointment.status: constants.listFieldValues.appointment.idByStatus[
                appointment.status
            ],
            constants.uf.appointment.code: constants.listFieldValues.appointment.idByCode[
                appointment.code
            ],
        }
        response = await BITRIX.call(
            "crm.item.add",
            {"entityTypeId": constants.entityTypeId.appointment, "fields": fields},
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response.get("id"):
            return AppointmentCreateResponse(
                id=response["id"],
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Bitrix: {response.get('error', 'Неизвестная ошибка')}",
            )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Недопустимый статус или код: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", status_code=200, response_model=Appointment)
async def get_appointment(id: int = Query(...)):
    try:
        response = await BITRIX.call(
            "crm.item.get",
            {
                "entityTypeId": constants.entityTypeId.appointment,
                "id": id,
                "useOriginalUfNames": "N",
            },
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response.get("id"):
            return Appointment.from_bitrix(response)
        else:
            raise HTTPException(status_code=404, detail="Запись не найдена")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", status_code=200)
async def update_appointment(appointment: AppointmentCreate, id: int = Query(...)):
    try:
        fields = {
            "ASSIGNED_BY_ID": appointment.specialist,
            constants.uf.appointment.patient: appointment.patient,
            constants.uf.appointment.start: appointment.start,
            constants.uf.appointment.end: appointment.end,
            constants.uf.appointment.status: constants.listFieldValues.appointment.idByStatus[
                appointment.status
            ],
            constants.uf.appointment.code: constants.listFieldValues.appointment.idByCode[
                appointment.code
            ],
        }
        response = await BITRIX.call(
            "crm.item.update",
            {
                "entityTypeId": constants.entityTypeId.appointment,
                "id": id,
                "fields": fields,
            },
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response.get("id"):
            return Appointment.from_bitrix(response)
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Bitrix: {response.get('error', 'Неизвестная ошибка')}",
            )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Недопустимый статус или код: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/", status_code=200)
async def delete_appointment(id: int = Query(...)):
    try:
        response = await BITRIX.call(
            "crm.item.delete",
            {"entityTypeId": constants.entityTypeId.appointment, "id": id},
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response == []:
            return True
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Bitrix: {response.get('error', 'Неизвестная ошибка')}",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
