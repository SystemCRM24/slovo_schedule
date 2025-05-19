from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from .models.schedule_models import WorkSchedule, WorkScheduleCreate, WorkScheduleCreateResponse
from .constants import constants
from app.bitrix import BITRIX
import logging

logging.basicConfig(level=logging.DEBUG)
router = APIRouter(prefix='/schedule', tags=["Schedule"])


# Преобразование даты из ISO в формат Bitrix
def iso_date_to_bitrix(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    return dt.strftime("%d.%m.%Y")

# Преобразование интервала из ISO в формат Bitrix
def interval_to_bitrix(intervals: List[str]) -> str:
    start_dt = datetime.fromisoformat(intervals[0].replace("+03:00", ""))
    end_dt = datetime.fromisoformat(intervals[1].replace("+03:00", ""))
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    return f"{start_ms}:{end_ms}"

# Преобразование списка интервалов из ISO в формат Bitrix
def intervals_to_bitrix(intervals: List[str]) -> List[str]:
    return [interval_to_bitrix(i) for i in intervals]

# Преобразование даты из формата Bitrix в ISO
def bitrix_date_to_iso(bitrix_date: str) -> Optional[str]:
    if bitrix_date:
        try:
            dt = datetime.fromisoformat(bitrix_date.replace("+03:00", ""))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            logging.error(f"Неверный формат даты Bitrix: {bitrix_date}")
            return None
    return None

# Преобразование интервала из формата Bitrix в ISO
def bitrix_to_interval(bitrix_str: str) -> List[str]:
    start_ms, end_ms = map(int, bitrix_str.split(":"))
    start_dt = datetime.fromtimestamp(start_ms / 1000)
    end_dt = datetime.fromtimestamp(end_ms / 1000)
    return [start_dt.isoformat() + "+03:00", end_dt.isoformat() + "+03:00"]

def bitrix_to_intervals(bitrix_list: List[str]) -> List[str]:
    return [bitrix_to_interval(s) for s in bitrix_list]

@router.post("/", status_code=201, response_model=WorkScheduleCreateResponse)
async def create_schedule(schedule: WorkScheduleCreate):
    try:
        fields = {
            "ASSIGNED_BY_ID": schedule.specialist,
            constants.uf.workSchedule.date: schedule.date,
            constants.uf.workSchedule.intervals: schedule.intervals,
        }
        response = await BITRIX.call(
            "crm.item.add",
            {"entityTypeId": constants.entityTypeId.workSchedule, "fields": fields},
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response.get("id"):
            return WorkScheduleCreateResponse(
                id=response["id"]
            )
        else:
            error = response.get("error", {})
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Bitrix: {error.get('error_description', 'Неизвестная ошибка')}",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", status_code=200, response_model=WorkSchedule)
async def get_schedule(id: int = Query(...)):
    try:
        response = await BITRIX.call(
            "crm.item.get",
            {
                "entityTypeId": constants.entityTypeId.workSchedule,
                "id": id,
                "useOriginalUfNames": "N",
            },
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response.get("id"):
            date_iso = bitrix_date_to_iso(response.get(constants.uf.workSchedule.date))
            intervals = bitrix_to_intervals(response.get(constants.uf.workSchedule.intervals, []))
            return WorkSchedule(
                id=response["id"],
                specialist=response["assignedById"],
                date=date_iso,
                intervals=intervals,
            )
        else:
            error = response.get("error", {})
            if error.get("error") == "ERROR_NO_DATA_FOUND":
                raise HTTPException(status_code=404, detail="Запись не найдена")
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка Bitrix: {error.get('error_description', 'Неизвестная ошибка')}",
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", status_code=200)
async def update_schedule(schedule: WorkScheduleCreate, id: int = Query(...)):
    try:
        date_bitrix = iso_date_to_bitrix(schedule.date)
        intervals_bitrix = intervals_to_bitrix(schedule.intervals)
        fields = {
            "ASSIGNED_BY_ID": schedule.specialist,
            constants.uf.workSchedule.date: date_bitrix,
            constants.uf.workSchedule.intervals: intervals_bitrix,
        }

        response = await BITRIX.call(
            "crm.item.update",
            {
                "entityTypeId": constants.entityTypeId.workSchedule,
                "id": id,
                "fields": fields,
            },
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response.get("id"):
            date_iso = bitrix_date_to_iso(response.get(constants.uf.workSchedule.date))
            intervals = bitrix_to_intervals(response.get(constants.uf.workSchedule.intervals, []))
            return WorkSchedule(
                id=response["id"],
                specialist=response["assignedById"],
                date=date_iso,
                intervals=intervals,
            )
        else:
            error = response.get("error", {})
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Bitrix: {error.get('error_description', 'Неизвестная ошибка')}",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/", status_code=200)
async def delete_schedule(id: int = Query(...)):
    try:
        response = await BITRIX.call(
            "crm.item.delete",
            {"entityTypeId": constants.entityTypeId.workSchedule, "id": id},
        )
        logging.debug(f"\n[ BITRIX RESPONSE ]\n{response}")
        if response == []:
            return {"message": "Успешно удалено"}
        else:
            error = response.get("error", {})
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Bitrix: {error.get('error_description', 'Неизвестная ошибка')}",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
