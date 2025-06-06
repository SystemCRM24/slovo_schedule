from datetime import datetime, timedelta
from typing import Self

from app.settings.main import settings


class Interval:
    __slots__ = ('start', 'end')

    @classmethod
    def from_timestamp(cls, start: float, end: float) -> Self:
        """Создает объект на основе таймстампов"""
        return cls(
            start=datetime.fromtimestamp(start, settings.TIMEZONE),
            end=datetime.fromtimestamp(end, settings.TIMEZONE)
        )
    
    @classmethod
    def from_js_timestamp(cls, start: int | str, end: int | str) -> Self:
        """Создает объект на основе таймстампов js формата"""
        map_obj = map(lambda x: float(x) / 1000, (start, end))
        return cls.from_timestamp(*map_obj)
    
    @classmethod
    def from_iso(cls, start: str, end: str) -> Self:
        return cls(
            start=datetime.fromisoformat(start),
            end=datetime.fromisoformat(end)
        )

    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(start={repr(self.start)}, end={repr(self.end)})'

    def __contains__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.start <= other <= self.end
        return self.start <= other.start and self.end >= other.end
    
    def __bool__(self) -> bool:
        return self.start < self.end
    
    def duration(self) -> timedelta:
        """Возвращает длительность интервала"""
        return self.end - self.start
