from datetime import datetime, timedelta
from typing import Self

from src.core.settings import Settings


class Interval:

    __slots__ = ('start', 'end')

    @classmethod
    def from_timestamp(cls, start: float, end: float) -> Self:
        """Создает объект на основе таймстампов"""
        start = datetime.fromtimestamp(start, Settings.TIMEZONE)
        end = datetime.fromtimestamp(end, Settings.TIMEZONE)
        return cls(start, end)
    
    @classmethod
    def from_js_timestamp(cls, start: int | str, end: int | str) -> Self:
        """Создает объект на основе таймстампов js формата"""
        map_obj = map(lambda x: float(x) / 1000, (start, end))
        return cls.from_timestamp(*map_obj)
    
    @classmethod
    def from_iso(cls, start: str, end: str) -> Self:
        start=datetime.fromisoformat(start)
        end=datetime.fromisoformat(end)
        return cls(start, end)

    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(start={self.start.isoformat()}, end={self.end.isoformat()})'

    def __contains__(self, other) -> bool:
        if isinstance(other, datetime):
            return self.start <= other <= self.end
        return self.start <= other.start and self.end >= other.end
    
    def __bool__(self) -> bool:
        return self.start < self.end
    
    def duration(self) -> timedelta:
        """Возвращает длительность интервала"""
        return self.end - self.start

    def is_intersecting(self, other) -> bool:
        """Возвращает True, если интервалы пересекаются и False, в отбратном случае."""
        if not isinstance(other, self.__class__):
            raise NotImplemented
        return self.start < other.end and self.end > other.start

    def difference(self, other) -> tuple[None, Self]:
        """Возвращает разницу интервалов"""
        first = second = None
        if self.is_intersecting(other):
            if self.start < other.start:
                first = self.__class__(self.start, other.start)
            if self.end > other.end:
                second = self.__class__(other.end, self.end)
        return first, second
