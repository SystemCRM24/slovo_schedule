from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from src.middleware import AppExceptionHandlerMiddleware
from src.utils import handle_http_exception
from src.description import description
from src.services import on_startup
from src.api import api_router
from src.appointplan import appointplan_router


app = FastAPI(title="AppointPlan", description=description)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AppExceptionHandlerMiddleware)

app.add_event_handler('startup', on_startup)
app.add_exception_handler(HTTPException, handle_http_exception)

app.include_router(appointplan_router)
app.include_router(api_router)


@app.get('/ping', status_code=200, tags=['Main'])
async def ping() -> str:
    return 'pong'
