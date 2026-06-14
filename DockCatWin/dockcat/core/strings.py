from __future__ import annotations

from enum import Enum
from typing import Optional

from .state import AppLanguage, CatState, OutingPhase, ReminderType
from .settings import AppSettings
from .outing import OutingCollectable, OutingEvent


class AppStrings:
    def __init__(self, language: AppLanguage = AppLanguage.CHINESE):
        self.lang = language

    def _cn(self, cn: str, en: str) -> str:
        return cn if self.lang == AppLanguage.CHINESE else en

    @property
    def settings_window_title(self) -> str:
        return self._cn("DockCat 设置", "DockCat Settings")

    @property
    def menu_pet(self) -> str:
        return self._cn("摸摸 (改变姿势)", "Pat pat (change pose)")

    @property
    def menu_go_out(self) -> str:
        return self._cn("出门玩吧 (专注模式)", "Play outdoor (focus mode)")

    @property
    def menu_settings(self) -> str:
        return self._cn("设置", "Settings")

    @property
    def menu_sleep(self) -> str:
        return self._cn("去睡觉吧 (退出应用)", "Go to sleep (quit)")

    def recall(self, cat_name: str) -> str:
        return self._cn(f"召回{cat_name}", f"Recall {cat_name}")

    def status_title(self, state: CatState) -> str:
        if state.name == "transitioning":
            return self._cn("过渡", "Transition")
        elif state.name == "walking":
            return self._cn("散步", "Walking")
        elif state.name == "resting":
            return self._cn("休息", "Resting")
        elif state.name == "dragged":
            return self._cn("被抱起", "Held")
        elif state.name == "dialogue":
            return self._cn("对话", "Dialogue")
        elif state.name == "outing":
            return self._cn("出门", "Outing")
        return ""

    @property
    def done(self) -> str:
        return self._cn("完成啦", "Done")

    @property
    def snooze_five_minutes(self) -> str:
        return self._cn("稍等5分钟", "Wait 5 min")

    @property
    def cancel(self) -> str:
        return self._cn("取消", "Cancel")

    @property
    def confirm(self) -> str:
        return self._cn("确认", "Confirm")

    @property
    def ok(self) -> str:
        return self._cn("好的", "OK")

    @property
    def minute_unit(self) -> str:
        return self._cn("分钟", "min")

    def ask_outing_duration(self, cat_name: str) -> str:
        return self._cn(f"要让{cat_name}出门多久呢？", f"How long should {cat_name} play outside?")

    @property
    def outing_primary(self) -> str:
        return self._cn("出门", "Go out")

    def outing_departure(self, settings: AppSettings) -> str:
        suffix = settings.outing_departure_message_suffix.strip()
        if self.lang == AppLanguage.CHINESE:
            return f"我出门啦，{settings.user_salutation}。{suffix}"
        return f"I'm heading out, {settings.user_salutation}. {suffix}"

    def outing_return_event(self, salutation: str, event: OutingEvent) -> str:
        desc = event.chinese_description if self.lang == AppLanguage.CHINESE else event.english_description
        return self._cn(f"{salutation}，我回来啦。{desc}", f"I'm back, {salutation}. {desc}")

    def outing_return_collectable(self, salutation: str) -> str:
        return self._cn(f"我回来啦，给{salutation}带了礼物", f"I'm back, {salutation}. I brought you a gift.")

    def outing_return_plain(self, salutation: str) -> str:
        return self._cn(f"{salutation}，我回来啦", f"I'm back, {salutation}.")

    @property
    def welcome_back(self) -> str:
        return self._cn("欢迎回来", "Welcome back")

    @property
    def receive_gift(self) -> str:
        return self._cn("收下礼物", "Take gift")

    def recall_confirmation(self, cat_name: str) -> str:
        return self._cn(
            f"提前召回会丢失可能的收藏品，确定要召回{cat_name}吗？",
            f"Recalling {cat_name} early will lose possible collectables. Recall now?"
        )

    def reminder_message(self, type_: ReminderType, salutation: str, suffix: str) -> str:
        if self.lang == AppLanguage.CHINESE:
            return f"{salutation}，{suffix}"
        return f"{salutation}, {suffix}"

    def collectable_name(self, collectable: OutingCollectable) -> str:
        return collectable.chinese_name if self.lang == AppLanguage.CHINESE else collectable.english_name

    @property
    def alert_cancel(self) -> str:
        return self._cn("取消", "Cancel")

    @property
    def asset_pack_alert_ok(self) -> str:
        return self._cn("好", "OK")

    # Settings
    @property
    def settings_save(self) -> str:
        return self._cn("保存", "Save")

    @property
    def settings_cat_name(self) -> str:
        return self._cn("宠物名字", "Pet name")

    @property
    def settings_salutation(self) -> str:
        return self._cn("对你的称呼", "Calls you")

    @property
    def settings_language(self) -> str:
        return self._cn("语言", "Language")

    @property
    def settings_scale(self) -> str:
        return self._cn("缩放", "Scale")

    @property
    def settings_start_position(self) -> str:
        return self._cn("起始出现位置", "Start position")

    @property
    def settings_reminder_section(self) -> str:
        return self._cn("提醒设置", "Reminders")

    @property
    def settings_reminder_enabled(self) -> str:
        return self._cn("开启提醒模式", "Enable reminders")

    @property
    def settings_water_reminder(self) -> str:
        return self._cn("喝水提醒", "Water reminder")

    @property
    def settings_movement_reminder(self) -> str:
        return self._cn("久坐提醒", "Stand up reminder")

    @property
    def settings_custom_reminder(self) -> str:
        return self._cn("自定义提醒", "Custom reminder")

    @property
    def settings_reminder_message(self) -> str:
        return self._cn("提醒文案", "Message")

    @property
    def settings_default_outing_duration(self) -> str:
        return self._cn("默认出门时长", "Default outing duration")

    @property
    def settings_state_section(self) -> str:
        return self._cn("状态参数", "State timing")

    @property
    def settings_rest_duration(self) -> str:
        return self._cn("休息时长 (分)", "Rest duration (min)")

    @property
    def settings_walk_duration(self) -> str:
        return self._cn("散步时长 (分)", "Walk duration (min)")

    @property
    def settings_walk_speed(self) -> str:
        return self._cn("散步基础速度", "Walk speed")

    @property
    def settings_about_section(self) -> str:
        return self._cn("关于", "About")

    @property
    def settings_out_departure_message(self) -> str:
        return self._cn("出门招呼文案", "Outing message")

    @property
    def settings_activity_scope(self) -> str:
        return self._cn("活动范围", "Activity area")

    @property
    def settings_scope_dock(self) -> str:
        return self._cn("任务栏边", "Taskbar edge")

    @property
    def settings_scope_desktop(self) -> str:
        return self._cn("整个桌面", "Desktop")
