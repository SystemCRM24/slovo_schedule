from fastapi import APIRouter

from .appointment import router as appointment_router
from .schedule import router as schedule_router
from .main import router as main_router


router = APIRouter(prefix="/front", tags=["api"])

router.include_router(appointment_router)
router.include_router(schedule_router)
router.include_router(main_router)
