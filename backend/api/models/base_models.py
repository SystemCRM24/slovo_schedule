from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class DateRange(BaseModel):
    start: datetime
    end: datetime

class SpecialistResponse(BaseModel):
    id: int
    name: str
    departments: List[str]

class ClientResponse(BaseModel):
    id: int
    full_name: str

class Patient(BaseModel):
    id: str
    type: str

class Appointment(BaseModel):
    id: int
    start: datetime
    end: datetime
    patient: Patient
    status: str

class ScheduleResponse(BaseModel):
    specialist_id: int
    date: datetime
    appointments: List[Appointment]

class WorkInterval(BaseModel):
    start: str
    end: str

class WorkSchedule(BaseModel):
    id: int
    intervals: List[WorkInterval]

class WorkScheduleResponse(BaseModel):
    specialist_id: int
    date: datetime
    schedule: WorkSchedule