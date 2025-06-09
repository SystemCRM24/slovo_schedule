from typing import Self
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


tz = ZoneInfo('Europe/Moscow')


class Interval:

    __slots__ = ('start', 'end')

    @classmethod
    def from_timestamp(cls, start: float, end: float) -> Self:
        """Создает объект на основе таймстампов"""
        start = datetime.fromtimestamp(start, tz)
        end = datetime.fromtimestamp(end, tz)
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

    def is_intersecting(self, other) -> bool:
        """Возвращает True, если интервалы пересекаются и False, в отбратном случае."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.start < other.end and self.end > other.start

    def intersection(self, other) -> Self | None:
        """Возвращает пересечение интервалов как новый объект интервала"""
        if self.is_intersecting(other):
            start = max(self.start, other.start)
            end = min(self.end, other.end)
            return self.__class__(start, end)


s = Interval.from_iso(
    "2025-05-05T09:00:00+03:00",
    "2025-05-05T18:00:00+03:00"
)
a = Interval.from_iso(
    "2025-05-05T09:00:00+03:00",
    "2025-05-05T19:00:00+03:00"
)

print(s.intersection(a))
