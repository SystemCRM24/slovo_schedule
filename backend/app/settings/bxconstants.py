import asyncio


class UserFields:
    class Deal:
        code = "UF_CRM_6800C01983990"
        duration = "UF_CRM_1746625717138"


class BXConstants:
    __instance = None
    UserFields = UserFields

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __init__(self):
        self.__lock = asyncio.Lock()

    async def update(self):
        """Обновляет значения"""
        async with self.__lock:
            pass
