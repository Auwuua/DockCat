from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


class OutingWakeResolver:
    """Resolve what to do when the app wakes up and finds an active outing."""

    class Resolution:
        pass

    class NoActiveOuting(Resolution):
        pass

    class Reschedule(Resolution):
        def __init__(self, remaining: float, planned_duration: float):
            self.remaining = remaining
            self.planned_duration = planned_duration

    class ReturnNow(Resolution):
        def __init__(self, planned_duration: float):
            self.planned_duration = planned_duration

    def resolution(self, end_date: Optional[datetime], planned_duration: Optional[float],
                   default_duration: float) -> Resolution:
        if end_date is None:
            return self.NoActiveOuting()

        now = datetime.now()
        if end_date > now:
            remaining = (end_date - now).total_seconds()
            return self.Reschedule(remaining, planned_duration or default_duration)
        else:
            return self.ReturnNow(planned_duration or default_duration)


class UsageStatistics:
    def __init__(self):
        self.first_use_date: Optional[str] = None
        self.total_usage_seconds: float = 0.0
        self.water_reminder_count: int = 0
        self.movement_reminder_count: int = 0
        self.outing_event_count: int = 0
        self.outing_collectable_count: int = 0

    def to_dict(self) -> dict:
        return {
            "first_use_date": self.first_use_date,
            "total_usage_seconds": self.total_usage_seconds,
            "water_reminder_count": self.water_reminder_count,
            "movement_reminder_count": self.movement_reminder_count,
            "outing_event_count": self.outing_event_count,
            "outing_collectable_count": self.outing_collectable_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UsageStatistics":
        stats = cls()
        stats.first_use_date = data.get("first_use_date")
        stats.total_usage_seconds = data.get("total_usage_seconds", 0)
        stats.water_reminder_count = data.get("water_reminder_count", 0)
        stats.movement_reminder_count = data.get("movement_reminder_count", 0)
        stats.outing_event_count = data.get("outing_event_count", 0)
        stats.outing_collectable_count = data.get("outing_collectable_count", 0)
        return stats
