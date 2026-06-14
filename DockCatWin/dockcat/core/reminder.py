from __future__ import annotations

import time
from typing import Optional

from .state import ReminderType
from .settings import AppSettings


class ReminderScheduler:
    def __init__(self, settings: AppSettings):
        self._settings = settings
        self._pending_reminder: Optional[ReminderType] = None
        self._next_water_due: Optional[float] = None
        self._next_movement_due: Optional[float] = None
        self._next_custom_due: Optional[float] = None
        if settings.reminders_enabled:
            self._reset_timers(time.time())

    @property
    def settings(self) -> AppSettings:
        return self._settings

    @property
    def pending_reminder(self) -> Optional[ReminderType]:
        return self._pending_reminder

    def update_settings(self, settings: AppSettings):
        previous = self._settings
        was_enabled = self._settings.reminders_enabled
        self._settings = settings
        if not settings.reminders_enabled:
            self.clear()
        elif not was_enabled:
            self._reset_timers(time.time())
        else:
            now = time.time()
            if previous.water_reminder_interval != settings.water_reminder_interval:
                self._next_water_due = now + settings.water_reminder_interval
            if previous.movement_reminder_interval != settings.movement_reminder_interval:
                self._next_movement_due = now + settings.movement_reminder_interval
            if not settings.custom_reminder_enabled:
                self._next_custom_due = None
                if self._pending_reminder == ReminderType.CUSTOM:
                    self._pending_reminder = None
            elif (not previous.custom_reminder_enabled or
                  previous.custom_reminder_interval != settings.custom_reminder_interval):
                self._next_custom_due = now + settings.custom_reminder_interval

    def due_reminder(self, is_long_duration: bool) -> Optional[ReminderType]:
        if not self._settings.reminders_enabled:
            return None
        if self._pending_reminder:
            return self._pending_reminder if is_long_duration else None

        now = time.time()
        water_due = self._next_water_due is not None and self._next_water_due <= now
        movement_due = self._next_movement_due is not None and self._next_movement_due <= now
        custom_due = (self._settings.custom_reminder_enabled and
                      self._next_custom_due is not None and self._next_custom_due <= now)

        if movement_due:
            due = ReminderType.MOVEMENT
        elif custom_due:
            due = ReminderType.CUSTOM
        elif water_due:
            due = ReminderType.WATER
        else:
            return None

        self._pending_reminder = due
        return due if is_long_duration else None

    def complete(self, type_: ReminderType):
        self._pending_reminder = None
        now = time.time()
        if type_ == ReminderType.WATER:
            self._next_water_due = now + self._settings.water_reminder_interval
        elif type_ == ReminderType.MOVEMENT:
            self._next_movement_due = now + self._settings.movement_reminder_interval
            self._next_water_due = now + self._settings.water_reminder_interval
        elif type_ == ReminderType.CUSTOM:
            if self._settings.custom_reminder_enabled:
                self._next_custom_due = now + self._settings.custom_reminder_interval
            else:
                self._next_custom_due = None

    def snooze(self, type_: ReminderType, interval: float = 5 * 60):
        self._pending_reminder = None
        due = time.time() + interval
        if type_ == ReminderType.WATER:
            self._next_water_due = due
        elif type_ == ReminderType.MOVEMENT:
            self._next_movement_due = due
            if self._next_water_due is not None and self._next_water_due <= due:
                self._next_water_due = due
        elif type_ == ReminderType.CUSTOM:
            if self._settings.custom_reminder_enabled:
                self._next_custom_due = due

    def clear(self):
        self._pending_reminder = None
        self._next_water_due = None
        self._next_movement_due = None
        self._next_custom_due = None

    def restart_timers_from_now(self):
        if self._settings.reminders_enabled:
            self._reset_timers(time.time())
        else:
            self.clear()

    def _reset_timers(self, from_time: float):
        self._pending_reminder = None
        self._next_water_due = from_time + self._settings.water_reminder_interval
        self._next_movement_due = from_time + self._settings.movement_reminder_interval
        self._next_custom_due = (
            from_time + self._settings.custom_reminder_interval
            if self._settings.custom_reminder_enabled
            else None
        )
