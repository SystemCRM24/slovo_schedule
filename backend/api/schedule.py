from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from .models.schedule_models import Interval, WorkSchedule, WorkScheduleCreate, WorkScheduleCreateResponse
from .constants import constants
from slovo_schedule.backend.app.bitrix import BITRIX

router = APIRouter(prefix='/schedule')


# Преобразование даты из ISO в формат Bitrix
def iso_date_to_bitrix(date_str: str) -> str:
    dt = datetime.fromisoformat(date_str.replace("+00:00", "")).date()
    return dt.strftime("%d.%m.%Y")


# Преобразование интервала из ISO в формат Bitrix
def interval_to_bitrix(interval: Interval) -> str:
    start_dt = datetime.fromisoformat(interval.start.replace("+00:00", ""))
    end_dt = datetime.fromisoformat(interval.end.replace("+00:00", ""))
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    return f"{start_ms}:{end_ms}"


# Преобразование списка интервалов из ISO в формат Bitrix
def intervals_to_bitrix(intervals: List[Interval]) -> List[str]:
    return [interval_to_bitrix(i) for i in intervals]


# Преобразование даты из формата Bitrix в ISO
def bitrix_date_to_iso(bitrix_date: str) -> Optional[str]:
    if bitrix_date:
        day, month, year = map(int, bitrix_date.split("."))
        return f"{year}-{month:02d}-{day:02d}"
    return None


# Преобразование интервала из формата Bitrix в ISO
def bitrix_to_interval(bitrix_str: str) -> Interval:
    start_ms, end_ms = map(int, bitrix_str.split(":"))
    start_dt = datetime.fromtimestamp(start_ms / 1000)
    end_dt = datetime.fromtimestamp(end_ms / 1000)
    return Interval(
        start=start_dt.isoformat() + "+00:00", end=end_dt.isoformat() + "+00:00"
    )


# Преобразование списка интервалов из формата Bitrix в ISO
def bitrix_to_intervals(bitrix_list: List[str]) -> List[Interval]:
    return [bitrix_to_interval(s) for s in bitrix_list]

@router.post("/", status_code=201, response_model=WorkScheduleCreateResponse)
async def create_schedule(schedule: WorkScheduleCreate):
    try:
        date_bitrix = iso_date_to_bitrix(schedule.date)
        intervals_bitrix = intervals_to_bitrix(schedule.intervals)
        fields = {
            "ASSIGNED_BY_ID": schedule.specialist,
            constants.uf.workSchedule.date: date_bitrix,
            constants.uf.workSchedule.intervals: intervals_bitrix,
        }
        response = await BITRIX.call(
            "crm.item.add",
            {"entityTypeId": constants.entityTypeId.workSchedule, "fields": fields},
        )
        if response.get("result"):
            return {"id": response["result"]}
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
        if response.get("result"):
            data = response["result"]
            date_iso = bitrix_date_to_iso(data.get(constants.uf.workSchedule.date))
            intervals = bitrix_to_intervals(
                data.get(constants.uf.workSchedule.intervals, [])
            )
            return WorkSchedule(
                id=data["ID"],
                specialist=data["ASSIGNED_BY_ID"],
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
        if response.get("result"):
            return {"message": "Успешно обновлено"}
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
        if response.get("result"):
            return {"message": "Успешно удалено"}
        else:
            error = response.get("error", {})
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка Bitrix: {error.get('error_description', 'Неизвестная ошибка')}",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
