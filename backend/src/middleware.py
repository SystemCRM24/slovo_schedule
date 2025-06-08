from typing import Coroutine

import asyncio
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback

from .logger import logger


class AppExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Логгирование ошибок приложения"""
    error_content = {'detail': 'Iternal Server Error'}
    
    @staticmethod
    def _log_app_exception(stack: traceback.StackSummary, trace_format: str):
        async def coro():
            error_location = 'unknown'
            for frame in reversed(stack):
                if frame.filename.endswith('.py') and "middleware" not in frame.filename.lower():
                    error_location = f"{frame.filename}:{frame.lineno} ({frame.name})"
                    break
            msg = f'{error_location}\n{trace_format}'
            logger.critical(msg)
        asyncio.create_task(coro())

    async def dispatch(self, request: Request, call_next: Coroutine):
        try:
            return await call_next(request)
        except Exception as app_exception:
            stack = traceback.extract_stack()
            trace_format = traceback.format_exc()
            self._log_app_exception(stack, trace_format)
            self.error_content['error'] = str(app_exception)
        return JSONResponse(status_code=500, content=self.error_content)
