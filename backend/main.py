from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from src.middleware import AppExceptionHandlerMiddleware
from src.utils import handle_http_exception
from src.description import description
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

app.include_router(appointplan_router)
app.include_router(api_router)

app.add_exception_handler(HTTPException, handle_http_exception)

# @app.exception_handler(HTTPException)
# async def handle_exception(request, exc: HTTPException):
#     pass


# app.add_exception_handler(Exception, lambda r, e: print(e))
