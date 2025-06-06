from fastapi import APIRouter


router = APIRouter(prefix="", tags=['AppointPlan'])


@router.post("/handle", status_code=200)
async def handle_appointments(data: str):
    # parsed_data = parse_query(data)
    # handler = Handler(parsed_data)
    # return await handle_appointments_v2(data)
    pass
