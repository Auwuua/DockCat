from __future__ import annotations

import json
import os
import time
from typing import Optional

from .state import AppLanguage, CatActivityScope, ReminderType


SETTINGS_FILE = "settings.json"


class AppSettings:
    def __init__(
        self,
        language: AppLanguage = AppLanguage.CHINESE,
        cat_name: str = "栗子",
        cat_identifier: str = "Lizz",
        user_salutation: str = "妈妈",
        selected_asset_pack_id: str = "default-lizz",
        reminders_enabled: bool = True,
        water_reminder_interval: float = 30 * 60,
        water_reminder_message_suffix: str = "该喝水啦",
        movement_reminder_interval: float = 60 * 60,
        movement_reminder_message_suffix: str = "该起来走走啦",
        custom_reminder_enabled: bool = False,
        custom_reminder_interval: float = 30 * 60,
        custom_reminder_message_suffix: str = "休息一下吧",
        outing_departure_message_suffix: str = "工作要加油呀！",
        default_outing_duration: float = 25 * 60,
        rest_duration_minimum: float = 2 * 60,
        rest_duration_maximum: float = 5 * 60,
        walk_duration_minimum: float = 2 * 60,
        walk_duration_maximum: float = 5 * 60,
        walk_base_speed: float = 36,
        cat_scale_percent: float = 15,
        start_position_percent: float = 75,
        cat_activity_scope: CatActivityScope = CatActivityScope.DOCK_EDGE,
        active_outing_end_date: Optional[float] = None,
        active_outing_duration: Optional[float] = None,
    ):
        self.language = language
        self.cat_name = cat_name
        self.cat_identifier = cat_identifier
        self.user_salutation = user_salutation
        self.selected_asset_pack_id = selected_asset_pack_id
        self.reminders_enabled = reminders_enabled
        self.water_reminder_interval = water_reminder_interval
        self.water_reminder_message_suffix = water_reminder_message_suffix
        self.movement_reminder_interval = movement_reminder_interval
        self.movement_reminder_message_suffix = movement_reminder_message_suffix
        self.custom_reminder_enabled = custom_reminder_enabled
        self.custom_reminder_interval = custom_reminder_interval
        self.custom_reminder_message_suffix = custom_reminder_message_suffix
        self.outing_departure_message_suffix = outing_departure_message_suffix
        self.default_outing_duration = default_outing_duration
        self.rest_duration_minimum = rest_duration_minimum
        self.rest_duration_maximum = rest_duration_maximum
        self.walk_duration_minimum = walk_duration_minimum
        self.walk_duration_maximum = walk_duration_maximum
        self.walk_base_speed = walk_base_speed
        self.cat_scale_percent = cat_scale_percent
        self.start_position_percent = start_position_percent
        self.cat_activity_scope = cat_activity_scope
        self.active_outing_end_date = active_outing_end_date
        self.active_outing_duration = active_outing_duration

    def reminder_message_suffix(self, type_: ReminderType) -> str:
        if type_ == ReminderType.WATER:
            return self.water_reminder_message_suffix
        elif type_ == ReminderType.MOVEMENT:
            return self.movement_reminder_message_suffix
        else:
            return self.custom_reminder_message_suffix

    def to_dict(self) -> dict:
        return {
            "language": self.language.value,
            "cat_name": self.cat_name,
            "cat_identifier": self.cat_identifier,
            "user_salutation": self.user_salutation,
            "selected_asset_pack_id": self.selected_asset_pack_id,
            "reminders_enabled": self.reminders_enabled,
            "water_reminder_interval": self.water_reminder_interval,
            "water_reminder_message_suffix": self.water_reminder_message_suffix,
            "movement_reminder_interval": self.movement_reminder_interval,
            "movement_reminder_message_suffix": self.movement_reminder_message_suffix,
            "custom_reminder_enabled": self.custom_reminder_enabled,
            "custom_reminder_interval": self.custom_reminder_interval,
            "custom_reminder_message_suffix": self.custom_reminder_message_suffix,
            "outing_departure_message_suffix": self.outing_departure_message_suffix,
            "default_outing_duration": self.default_outing_duration,
            "rest_duration_minimum": self.rest_duration_minimum,
            "rest_duration_maximum": self.rest_duration_maximum,
            "walk_duration_minimum": self.walk_duration_minimum,
            "walk_duration_maximum": self.walk_duration_maximum,
            "walk_base_speed": self.walk_base_speed,
            "cat_scale_percent": self.cat_scale_percent,
            "start_position_percent": self.start_position_percent,
            "cat_activity_scope": self.cat_activity_scope.value,
            "active_outing_end_date": self.active_outing_end_date,
            "active_outing_duration": self.active_outing_duration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        return cls(
            language=AppLanguage(data.get("language", "chinese")),
            cat_name=data.get("cat_name", "栗子"),
            cat_identifier=data.get("cat_identifier", "Lizz"),
            user_salutation=data.get("user_salutation", "妈妈"),
            selected_asset_pack_id=data.get("selected_asset_pack_id", "default-lizz"),
            reminders_enabled=data.get("reminders_enabled", True),
            water_reminder_interval=data.get("water_reminder_interval", 30 * 60),
            water_reminder_message_suffix=data.get("water_reminder_message_suffix", "该喝水啦"),
            movement_reminder_interval=data.get("movement_reminder_interval", 60 * 60),
            movement_reminder_message_suffix=data.get("movement_reminder_message_suffix", "该起来走走啦"),
            custom_reminder_enabled=data.get("custom_reminder_enabled", False),
            custom_reminder_interval=data.get("custom_reminder_interval", 30 * 60),
            custom_reminder_message_suffix=data.get("custom_reminder_message_suffix", "休息一下吧"),
            outing_departure_message_suffix=data.get("outing_departure_message_suffix", "工作要加油呀！"),
            default_outing_duration=data.get("default_outing_duration", 25 * 60),
            rest_duration_minimum=data.get("rest_duration_minimum", 2 * 60),
            rest_duration_maximum=data.get("rest_duration_maximum", 5 * 60),
            walk_duration_minimum=data.get("walk_duration_minimum", 2 * 60),
            walk_duration_maximum=data.get("walk_duration_maximum", 5 * 60),
            walk_base_speed=data.get("walk_base_speed", 36),
            cat_scale_percent=data.get("cat_scale_percent", 15),
            start_position_percent=data.get("start_position_percent", 75),
            cat_activity_scope=CatActivityScope(data.get("cat_activity_scope", "dockEdge")),
            active_outing_end_date=data.get("active_outing_end_date"),
            active_outing_duration=data.get("active_outing_duration"),
        )


class SettingsStore:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".dockcat")
        self._data_dir = data_dir
        self._file_path = os.path.join(data_dir, SETTINGS_FILE)
        os.makedirs(data_dir, exist_ok=True)

    def load(self) -> AppSettings:
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppSettings.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return AppSettings()

    def save(self, settings: AppSettings):
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, ensure_ascii=False, indent=2)
