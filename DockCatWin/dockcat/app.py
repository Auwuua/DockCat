from __future__ import annotations

import math
import os
import random
import time
from typing import Optional, Callable

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .core.state import (
    CatState, ReminderType, OutingPhase, AppLanguage, CatActivityScope,
    resting, walking, transitioning, dragged, dialogue, outing
)
from .core.state_machine import CatStateMachine
from .core.settings import AppSettings, SettingsStore
from .core.strings import AppStrings
from .core.assets import AssetPackLoader
from .core.animation import PoseRenderer, SpriteAnimator
from .core.reminder import ReminderScheduler
from .core.outing import (
    OutingCatalogLoader, OutingRewardGenerator, CollectableInventory
)
from .core.activity_space import ActivitySpace, get_current_activity_space
from .ui.cat_window import CatWindow
from .ui.interaction import CatInteraction
from .ui.tray import TrayManager
from .ui.settings_dialog import SettingsDialog


class DockCatApplication:
    """Main application controller - ties everything together."""

    @property
    def _resources_dir(self) -> str:
        return os.path.join(os.path.dirname(__file__), "resources")

    def __init__(self):
        self._settings_store = SettingsStore()
        self._settings = self._settings_store.load()
        self._strings = AppStrings(self._settings.language)

        # Activity space
        self._activity_space = get_current_activity_space(
            self._settings.start_position_percent
        )

        # Assets
        resources_dir = os.path.join(os.path.dirname(__file__), "resources")
        self._asset_loader = AssetPackLoader(
            os.path.join(self._resources_dir, "CatPacks"),
            default_dir=os.path.join(self._resources_dir, "DefaultCat"),
        )
        self._default_pack = self._asset_loader.load_default_pack()
        self._asset_pack = self._asset_loader.load_selected_pack(
            self._settings.selected_asset_pack_id
        )
        if self._asset_pack is None:
            self._asset_pack = self._default_pack
        self._renderer = PoseRenderer(self._asset_pack, self._default_pack)

        # Outing
        self._outing_catalog_loader = OutingCatalogLoader(
            os.path.join(self._resources_dir, "Outing")
        )
        self._outing_catalog = self._outing_catalog_loader.load_catalog()
        self._collectable_inventory = CollectableInventory()

        # UI
        self._cat_window = CatWindow()
        self._interaction = CatInteraction(self._cat_window)
        self._tray = TrayManager(self._cat_window)
        self._settings_dialog = None

        # Animation
        self._walk_animator = SpriteAnimator()

        # Reminder
        self._reminder_scheduler = ReminderScheduler(self._settings)

        # State machine
        self._walker_direction: float = 1.0
        self._state_end_time: Optional[float] = None
        self._pending_outing_duration: Optional[float] = None
        self._pending_outing_reward = None
        self._should_use_start_position = False

        self._state_machine: Optional[CatStateMachine] = None
        self._reminder_timer: Optional[QTimer] = None
        self._walk_movement_timer: Optional[QTimer] = None
        self._outing_timer: Optional[QTimer] = None
        self._startup_timer: Optional[QTimer] = None

    def start(self):
        """Start the application."""
        self._configure_interaction()
        self._configure_tray()

        self._state_machine = self._make_state_machine()
        self._state_machine.on_transition = self._on_state_transition
        self._state_machine.on_duration_scheduled = self._on_duration_scheduled

        # Start after a brief delay
        self._startup_timer = QTimer()
        self._startup_timer.setSingleShot(True)
        self._startup_timer.timeout.connect(self._do_startup)
        self._startup_timer.start(1000)

        self._start_reminder_polling()

    def _do_startup(self):
        self._should_use_start_position = True
        self._state_machine.start()

    def _make_state_machine(self) -> CatStateMachine:
        return CatStateMachine(
            initial_position=self._start_position_anchor(),
            entrance_provider=self._start_position_anchor,
            walking_duration_range=(
                max(1, self._settings.walk_duration_minimum),
                max(1, self._settings.walk_duration_maximum),
            ),
            resting_duration_range=(
                max(1, self._settings.rest_duration_minimum),
                max(1, self._settings.rest_duration_maximum),
            ),
        )

    def _configure_interaction(self):
        self._interaction.on_context_menu = self._show_context_menu
        self._interaction.on_begin_drag = lambda: self._state_machine.begin_drag()
        self._interaction.on_drag = self._on_drag
        self._interaction.on_end_drag = self._on_end_drag

    def _configure_tray(self):
        self._tray.on_pet = self._pet_cat
        self._tray.on_outing = lambda: self._state_machine.begin_outing_prompt()
        self._tray.on_settings = self._show_settings
        self._tray.on_quit = QApplication.instance().quit
        self._tray.on_recall = self._show_recall_confirmation
        self._tray.set_language(self._settings.language)
        self._tray.build_menu()

    def _show_context_menu(self, event):
        self._tray.build_menu(self._state_machine.state if self._state_machine else None)
        # For system tray, right-click on tray icon already shows menu
        # For cat right-click, we use the tray approach
        tray = self._tray._tray
        if tray and tray.isVisible():
            tray.show()

    def _pet_cat(self):
        if not self._state_machine:
            return
        state = self._state_machine.state
        if state.name == "resting":
            pose_img, mirrored = self._renderer.random_pose("resting", "dialogue")
            self._cat_window.set_image(pose_img, mirrored)
        elif state.name == "walking":
            self._walker_direction *= -1
            self._cat_window.set_mirrored(self._walker_direction < 0)

    def _on_drag(self, point: tuple[float, float]):
        if not self._state_machine:
            return
        state = self._state_machine.state
        if state.name == "outing" and state.params.get("phase") in (
            OutingPhase.LEAVING, OutingPhase.RETURNING
        ):
            return
        clamped = self._clamped_cat_point(point)
        self._state_machine.update_visible_position(clamped)
        self._cat_window.set_anchor(clamped)

    def _on_end_drag(self, point: tuple[float, float]):
        if not self._state_machine:
            return
        state = self._state_machine.state
        if state.name == "outing" and state.params.get("phase") in (
            OutingPhase.LEAVING, OutingPhase.RETURNING
        ):
            return
        clamped = self._clamped_cat_point(point)
        if self._state_machine.state.name == "dragged":
            self._state_machine.end_drag(clamped)
        else:
            self._state_machine.update_visible_position(clamped)
            self._cat_window.set_anchor(clamped)

    def _on_state_transition(self, old_state: CatState, new_state: CatState):
        self._stop_walk()
        self._state_end_time = None

        if new_state.name == "transitioning":
            self._cat_window.hide_bubble()
            pose_img, mirrored = self._renderer.random_pose("transition", "dialogue")
            self._cat_window.set_image(pose_img, mirrored)
            if self._should_use_start_position:
                point = self._start_position_anchor()
                self._should_use_start_position = False
            else:
                point = self._clamped_cat_point(self._state_machine.position)
            self._state_machine.update_visible_position(point)
            self._cat_window.show_at(point)

        elif new_state.name == "walking":
            self._cat_window.hide_bubble()
            self._start_walk()

        elif new_state.name == "resting":
            self._cat_window.hide_bubble()
            pose_img, mirrored = self._renderer.random_pose("resting", "dialogue")
            self._cat_window.set_image(pose_img, mirrored)
            point = self._clamped_cat_point(self._state_machine.position)
            self._state_machine.update_long_duration_position(point)
            self._cat_window.show_at(point)

        elif new_state.name == "dragged":
            self._cat_window.hide_bubble()
            pose_img, mirrored = self._renderer.random_pose("held", "dialogue")
            self._cat_window.set_image(pose_img, mirrored)

        elif new_state.name == "dialogue":
            pose_img, mirrored = self._renderer.random_pose("dialogue")
            self._cat_window.set_image(pose_img, mirrored)
            point = self._clamped_cat_point(self._state_machine.position)
            self._state_machine.update_visible_position(point)
            self._cat_window.show_at(point)
            self._show_reminder(new_state.params["type"])

        elif new_state.name == "outing":
            self._apply_outing_phase(new_state.params["phase"])

    def _on_duration_scheduled(self, state: CatState, duration: float):
        self._state_end_time = time.time() + duration
        QTimer.singleShot(int(duration * 1000), lambda: self._on_duration_finished(state))

    def _on_duration_finished(self, scheduled_state: CatState):
        if self._state_machine:
            self._state_machine.finish_scheduled_state(scheduled_state)

    def _show_reminder(self, type_: ReminderType):
        msg = self._strings.reminder_message(
            type_, self._settings.user_salutation,
            self._settings.reminder_message_suffix(type_)
        )
        self._cat_window.show_bubble(
            msg, self._strings.done, self._strings.snooze_five_minutes
        )
        self._cat_window.bubble.set_callbacks(
            on_primary=lambda: self._complete_reminder(type_),
            on_secondary=lambda: self._snooze_reminder(type_),
        )

    def _complete_reminder(self, type_: ReminderType):
        self._reminder_scheduler.complete(type_)
        self._cat_window.hide_bubble()
        self._state_machine.finish_reminder()

    def _snooze_reminder(self, type_: ReminderType):
        self._reminder_scheduler.snooze(type_)
        self._cat_window.hide_bubble()
        self._state_machine.finish_reminder()

    def _apply_outing_phase(self, phase: OutingPhase):
        if phase == OutingPhase.ASKING:
            pose_img, mirrored = self._renderer.random_pose("dialogue")
            self._cat_window.set_image(pose_img, mirrored)
            self._cat_window.show_at(self._clamped_cat_point(self._state_machine.position))
            self._ask_outing_duration()

        elif phase == OutingPhase.CONFIRMING_DEPARTURE:
            self._cat_window.show_at(self._clamped_cat_point(self._state_machine.position))
            self._cat_window.show_bubble(
                self._strings.outing_departure(self._settings),
                self._strings.ok
            )
            self._cat_window.bubble.set_callbacks(
                on_primary=self._start_confirmed_outing
            )

        elif phase == OutingPhase.LEAVING:
            self._start_outing_walk_out()

        elif phase == OutingPhase.AWAY:
            self._cat_window.hide()

        elif phase == OutingPhase.RETURNING:
            self._start_outing_walk_in()

        elif phase == OutingPhase.RETURNED:
            pose_img, mirrored = self._renderer.random_pose("dialogue")
            self._cat_window.set_image(pose_img, mirrored)
            self._show_outing_return_bubble()

    def _ask_outing_duration(self):
        msg = self._strings.ask_outing_duration(self._settings.cat_name)
        default_min = int(self._settings.default_outing_duration / 60)
        self._cat_window.show_input_bubble(
            msg, str(default_min),
            self._strings.outing_primary, self._strings.cancel,
            self._strings.minute_unit
        )
        self._cat_window.bubble.set_callbacks(
            on_value=self._confirm_outing_minutes,
            on_secondary=self._cancel_outing,
        )

    def _confirm_outing_minutes(self, text: str):
        try:
            minutes = max(1, int(text))
        except ValueError:
            minutes = int(self._settings.default_outing_duration / 60)
        self._pending_outing_duration = minutes * 60
        self._state_machine.confirm_outing()

    def _cancel_outing(self):
        self._cat_window.hide_bubble()
        self._state_machine.enter_random_long_duration_state()

    def _start_confirmed_outing(self):
        duration = self._pending_outing_duration or self._settings.default_outing_duration
        self._cat_window.hide_bubble()
        self._settings.active_outing_end_date = time.time() + duration
        self._settings.active_outing_duration = duration
        self._settings_store.save(self._settings)
        self._reminder_scheduler.clear()
        self._stop_reminder_polling()
        self._schedule_outing_return(duration)
        self._pending_outing_duration = None
        self._state_machine.depart_outing()

    def _schedule_outing_return(self, interval: float):
        if self._outing_timer:
            self._outing_timer.stop()
        self._outing_timer = QTimer()
        self._outing_timer.setSingleShot(True)
        self._outing_timer.timeout.connect(
            lambda: self._return_from_outing(draw_reward=True)
        )
        self._outing_timer.start(int(max(100, interval * 1000)))

    def _return_from_outing(self, draw_reward: bool = False, force_event: bool = False,
                            planned_duration: Optional[float] = None):
        if self._outing_timer:
            self._outing_timer.stop()
        if force_event:
            self._prepare_outing_event()
        elif draw_reward:
            self._prepare_outing_reward(
                planned_duration or self._settings.active_outing_duration or self._settings.default_outing_duration
            )
        else:
            self._pending_outing_reward = None
        self._settings.active_outing_end_date = None
        self._settings.active_outing_duration = None
        self._settings_store.save(self._settings)
        self._state_machine.return_from_outing()

    def _prepare_outing_reward(self, planned_duration: float):
        generator = OutingRewardGenerator(self._outing_catalog)
        reward = generator.reward(planned_duration)
        if reward is None:
            self._pending_outing_reward = None
            return
        self._pending_outing_reward = reward
        if reward.kind == "collectable" and reward.collectable:
            self._collectable_inventory.record_collectable(reward.collectable.id)

    def _prepare_outing_event(self):
        generator = OutingRewardGenerator(self._outing_catalog)
        reward = generator.event_reward()
        self._pending_outing_reward = reward

    def _show_outing_return_bubble(self):
        reward = self._pending_outing_reward
        if reward is None:
            self._cat_window.show_bubble(
                self._strings.outing_return_plain(self._settings.user_salutation),
                self._strings.welcome_back
            )
            self._cat_window.bubble.set_callbacks(on_primary=self._finish_outing_return)
        elif reward.kind == "event" and reward.event:
            self._cat_window.show_bubble(
                self._strings.outing_return_event(self._settings.user_salutation, reward.event),
                self._strings.welcome_back
            )
            self._cat_window.bubble.set_callbacks(on_primary=self._finish_outing_return)
        elif reward.kind == "collectable" and reward.collectable:
            collectable = reward.collectable
            img_path = self._outing_catalog_loader.image_url(collectable)
            pix = QPixmap(img_path) if os.path.exists(img_path) else None
            self._cat_window.show_image_bubble(
                self._strings.outing_return_collectable(self._settings.user_salutation),
                pix,
                self._strings.collectable_name(collectable),
                self._strings.receive_gift
            )
            self._cat_window.bubble.set_callbacks(on_primary=self._finish_outing_return)

    def _finish_outing_return(self):
        self._pending_outing_reward = None
        self._cat_window.hide_bubble()
        self._state_machine.welcome_back()
        self._reminder_scheduler.restart_timers_from_now()
        self._start_reminder_polling()

    def _show_recall_confirmation(self):
        if not self._state_machine or self._state_machine.state.name != "outing":
            return
        pose_img, mirrored = self._renderer.random_pose("dialogue")
        self._cat_window.set_image(pose_img, mirrored)
        self._cat_window.show_at(self._start_position_anchor())
        self._cat_window.show_bubble(
            self._strings.recall_confirmation(self._settings.cat_name),
            self._strings.confirm, self._strings.cancel
        )
        self._cat_window.bubble.set_callbacks(
            on_primary=self._do_recall,
            on_secondary=lambda: (
                self._cat_window.hide_bubble(),
                self._cat_window.hide()
            ),
        )

    def _do_recall(self):
        self._cat_window.hide_bubble()
        self._return_from_outing(force_event=True)

    def _start_walk(self):
        animation = self._renderer.animation_frames("walk")
        self._walker_direction = random.choice([-1, 1])
        first_frame = animation.frames[0] if animation.frames else self._renderer.first_image("dialogue")
        self._cat_window.set_image(first_frame, self._walker_direction < 0)
        start_pos = self._clamped_cat_point(self._state_machine.position)
        self._state_machine.update_long_duration_position(start_pos)
        self._cat_window.show_at(start_pos)

        self._walk_animator.start(animation, self._on_walk_frame)

        self._walk_movement_timer = QTimer()
        self._walk_movement_timer.timeout.connect(self._advance_walk)
        self._walk_movement_timer.start(int(1000 / 30))

    def _on_walk_frame(self, frame_index: int):
        animation = self._renderer.animation_frames("walk")
        if 0 <= frame_index < len(animation.frames):
            self._cat_window.set_image(animation.frames[frame_index], self._walker_direction < 0)

    def _advance_walk(self):
        if not self._state_machine or self._state_machine.state.name != "walking":
            return
        speed = self._settings.walk_base_speed / 30.0
        walk_range = self._activity_space.walk_range_for_content(
            self._cat_window.cat_view.width(),
            self._settings.cat_activity_scope
        )
        cur_x, cur_y = self._state_machine.position
        next_x = cur_x + self._walker_direction * speed

        if next_x <= walk_range[0]:
            next_x = walk_range[0]
            self._walker_direction = 1
        elif next_x >= walk_range[1]:
            next_x = walk_range[1]
            self._walker_direction = -1

        point = self._clamped_cat_point((next_x, cur_y))
        self._state_machine.update_long_duration_position(point)
        self._cat_window.set_anchor(point)
        self._cat_window.set_mirrored(self._walker_direction < 0)

    def _start_outing_walk_out(self):
        animation = self._renderer.animation_frames("walk")
        first_frame = animation.frames[0] if animation.frames else self._renderer.first_image("dialogue")
        self._cat_window.set_image(first_frame, False)
        start_pos = self._clamped_cat_point(self._state_machine.position)
        self._state_machine.update_outing_walk_position(start_pos)
        self._walker_direction = 1
        self._cat_window.show_at(start_pos)

        self._walk_animator.start(animation, self._on_walk_frame)

        self._walk_movement_timer = QTimer()
        self._walk_movement_timer.timeout.connect(self._advance_outing_walk_out)
        self._walk_movement_timer.start(int(1000 / 30))

    def _advance_outing_walk_out(self):
        if not self._state_machine or not (
            self._state_machine.state.name == "outing" and
            self._state_machine.state.params.get("phase") == OutingPhase.LEAVING
        ):
            return
        speed = self._settings.walk_base_speed * 1.5 / 30.0
        cur_x, cur_y = self._state_machine.position
        target_x = (self._activity_space.screen_frame[0] +
                     self._activity_space.screen_frame[2] +
                     self._cat_window.cat_view.width())
        next_x = cur_x + speed
        if next_x >= target_x:
            self._stop_walk()
            self._cat_window.hide()
            self._state_machine.update_outing_walk_position((target_x, cur_y))
            self._state_machine.mark_away()
            return
        self._state_machine.update_outing_walk_position((next_x, cur_y))
        self._cat_window.set_anchor((next_x, cur_y))
        self._cat_window.set_mirrored(False)

    def _start_outing_walk_in(self):
        animation = self._renderer.animation_frames("walk")
        first_frame = animation.frames[0] if animation.frames else self._renderer.first_image("dialogue")
        self._cat_window.set_image(first_frame, True)
        sx, sy, sw, sh = self._activity_space.screen_frame
        start_pos = (sx + sw + self._cat_window.cat_view.width(),
                      self._activity_space.baseline_y)
        self._state_machine.update_outing_walk_position(start_pos)
        self._walker_direction = -1
        self._cat_window.show_at(start_pos)

        self._walk_animator.start(animation, self._on_walk_frame)

        self._walk_movement_timer = QTimer()
        self._walk_movement_timer.timeout.connect(self._advance_outing_walk_in)
        self._walk_movement_timer.start(int(1000 / 30))

    def _advance_outing_walk_in(self):
        if not self._state_machine or not (
            self._state_machine.state.name == "outing" and
            self._state_machine.state.params.get("phase") == OutingPhase.RETURNING
        ):
            return
        speed = self._settings.walk_base_speed * 1.5 / 30.0
        cur_x, cur_y = self._state_machine.position
        target_x = self._start_position_anchor()[0]
        next_x = cur_x - speed
        if next_x <= target_x:
            self._state_machine.update_outing_walk_position((target_x, self._activity_space.baseline_y))
            self._cat_window.set_anchor((target_x, self._activity_space.baseline_y))
            self._cat_window.set_mirrored(True)
            self._stop_walk()
            self._state_machine.finish_return_walk()
            return
        self._state_machine.update_outing_walk_position((next_x, self._activity_space.baseline_y))
        self._cat_window.set_anchor((next_x, self._activity_space.baseline_y))
        self._cat_window.set_mirrored(True)

    def _stop_walk(self):
        self._walk_animator.stop()
        if self._walk_movement_timer:
            self._walk_movement_timer.stop()
            self._walk_movement_timer = None

    def _start_reminder_polling(self):
        if self._reminder_timer:
            return
        self._reminder_timer = QTimer()
        self._reminder_timer.timeout.connect(self._check_reminder)
        self._reminder_timer.start(10000)

    def _stop_reminder_polling(self):
        if self._reminder_timer:
            self._reminder_timer.stop()
            self._reminder_timer = None

    def _check_reminder(self):
        if not self._state_machine:
            return
        reminder = self._reminder_scheduler.due_reminder(
            self._state_machine.state.is_long_duration
        )
        if reminder is not None:
            self._state_machine.request_reminder(reminder)

    def _show_settings(self):
        if self._settings_dialog and self._settings_dialog.isVisible():
            self._settings_dialog.raise_()
            return
        dialog = SettingsDialog(self._settings, self._strings, self._cat_window)
        if dialog.exec() == SettingsDialog.Accepted and dialog.result_settings:
            old_lang = self._settings.language
            old_scope = self._settings.cat_activity_scope
            self._settings = dialog.result_settings
            self._settings_store.save(self._settings)
            self._strings = AppStrings(self._settings.language)
            self._tray.set_language(self._settings.language)
            self._tray.build_menu()
            self._reminder_scheduler.update_settings(self._settings)
            self._activity_space = get_current_activity_space(
                self._settings.start_position_percent
            )
            point = self._clamped_cat_point(self._state_machine.position)
            self._state_machine.update_visible_position(point)
            self._cat_window.set_anchor(point)

    def _start_position_anchor(self) -> tuple[float, float]:
        return self._anchor_point(self._activity_space.entrance_point[0])

    def _anchor_point(self, center_x: float) -> tuple[float, float]:
        cat_w = self._cat_window.cat_view.width()
        return (
            center_x - cat_w / 2,
            self._activity_space.baseline_y
        )

    def _clamped_cat_point(self, point: tuple[float, float]) -> tuple[float, float]:
        return self._activity_space.clamped_point(
            point,
            (self._cat_window.cat_view.width(), self._cat_window.cat_view.height()),
            self._settings.cat_activity_scope
        )
