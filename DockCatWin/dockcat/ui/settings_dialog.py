from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QSlider, QDialogButtonBox, QTabWidget, QWidget,
    QScrollArea, QGridLayout, QGroupBox, QTextEdit
)

from ..core.state import AppLanguage, CatActivityScope
from ..core.settings import AppSettings, SettingsStore
from ..core.strings import AppStrings


class SettingsDialog(QDialog):
    """Settings dialog with tabs."""

    def __init__(self, settings: AppSettings, strings: AppStrings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._strings = strings
        self._result_settings: Optional[AppSettings] = None
        self.setWindowTitle(strings.settings_window_title)
        self.setMinimumWidth(400)
        self._setup_ui()

    @property
    def result_settings(self) -> Optional[AppSettings]:
        return self._result_settings

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # Pet tab
        pet_tab = QWidget()
        pet_layout = QFormLayout(pet_tab)

        self._cat_name_edit = QLineEdit(self._settings.cat_name)
        pet_layout.addRow(self._strings.settings_cat_name, self._cat_name_edit)

        self._salutation_edit = QLineEdit(self._settings.user_salutation)
        pet_layout.addRow(self._strings.settings_salutation, self._salutation_edit)

        self._lang_combo = QComboBox()
        self._lang_combo.addItem("中文", AppLanguage.CHINESE)
        self._lang_combo.addItem("English", AppLanguage.ENGLISH)
        idx = self._lang_combo.findData(self._settings.language)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        pet_layout.addRow(self._strings.settings_language, self._lang_combo)

        self._scale_spin = QSpinBox()
        self._scale_spin.setRange(1, 100)
        self._scale_spin.setValue(int(self._settings.cat_scale_percent))
        self._scale_spin.setSuffix("%")
        pet_layout.addRow(self._strings.settings_scale, self._scale_spin)

        self._scope_combo = QComboBox()
        self._scope_combo.addItem(self._strings.settings_scope_dock, CatActivityScope.DOCK_EDGE)
        self._scope_combo.addItem(self._strings.settings_scope_desktop, CatActivityScope.DESKTOP)
        idx = self._scope_combo.findData(self._settings.cat_activity_scope)
        if idx >= 0:
            self._scope_combo.setCurrentIndex(idx)
        pet_layout.addRow(self._strings.settings_activity_scope, self._scope_combo)

        self._start_pos_spin = QSpinBox()
        self._start_pos_spin.setRange(0, 100)
        self._start_pos_spin.setValue(int(self._settings.start_position_percent))
        self._start_pos_spin.setSuffix("%")
        pet_layout.addRow(self._strings.settings_start_position, self._start_pos_spin)

        tabs.addTab(pet_tab, self._strings.menu_pet if self._settings.language == AppLanguage.CHINESE else "Pet")

        # Reminder tab
        reminder_tab = QWidget()
        reminder_layout = QFormLayout(reminder_tab)

        self._reminder_enabled_check = QCheckBox()
        self._reminder_enabled_check.setChecked(self._settings.reminders_enabled)
        reminder_layout.addRow(self._strings.settings_reminder_enabled, self._reminder_enabled_check)

        self._water_interval_spin = QSpinBox()
        self._water_interval_spin.setRange(1, 480)
        self._water_interval_spin.setValue(int(self._settings.water_reminder_interval / 60))
        self._water_interval_spin.setSuffix(" " + self._strings.minute_unit)
        reminder_layout.addRow(self._strings.settings_water_reminder + " " + self._strings.minute_unit, self._water_interval_spin)

        self._water_msg_edit = QLineEdit(self._settings.water_reminder_message_suffix)
        reminder_layout.addRow(self._strings.settings_water_reminder + " " + self._strings.settings_reminder_message, self._water_msg_edit)

        self._move_interval_spin = QSpinBox()
        self._move_interval_spin.setRange(1, 480)
        self._move_interval_spin.setValue(int(self._settings.movement_reminder_interval / 60))
        self._move_interval_spin.setSuffix(" " + self._strings.minute_unit)
        reminder_layout.addRow(self._strings.settings_movement_reminder + " " + self._strings.minute_unit, self._move_interval_spin)

        self._move_msg_edit = QLineEdit(self._settings.movement_reminder_message_suffix)
        reminder_layout.addRow(self._strings.settings_movement_reminder + " " + self._strings.settings_reminder_message, self._move_msg_edit)

        self._outing_msg_edit = QLineEdit(self._settings.outing_departure_message_suffix)
        reminder_layout.addRow(self._strings.settings_out_departure_message, self._outing_msg_edit)

        self._outing_duration_spin = QSpinBox()
        self._outing_duration_spin.setRange(1, 480)
        self._outing_duration_spin.setValue(int(self._settings.default_outing_duration / 60))
        self._outing_duration_spin.setSuffix(" " + self._strings.minute_unit)
        reminder_layout.addRow(self._strings.settings_default_outing_duration, self._outing_duration_spin)

        tabs.addTab(reminder_tab, self._strings.settings_reminder_section)

        # State timing tab
        state_tab = QWidget()
        state_layout = QFormLayout(state_tab)

        self._rest_min_spin = QSpinBox()
        self._rest_min_spin.setRange(1, 60)
        self._rest_min_spin.setValue(int(self._settings.rest_duration_minimum / 60))
        self._rest_min_spin.setSuffix(" " + self._strings.minute_unit)
        state_layout.addRow(self._strings.settings_rest_duration + " (min)", self._rest_min_spin)

        self._rest_max_spin = QSpinBox()
        self._rest_max_spin.setRange(1, 60)
        self._rest_max_spin.setValue(int(self._settings.rest_duration_maximum / 60))
        self._rest_max_spin.setSuffix(" " + self._strings.minute_unit)
        state_layout.addRow(self._strings.settings_rest_duration + " (max)", self._rest_max_spin)

        self._walk_min_spin = QSpinBox()
        self._walk_min_spin.setRange(1, 60)
        self._walk_min_spin.setValue(int(self._settings.walk_duration_minimum / 60))
        self._walk_min_spin.setSuffix(" " + self._strings.minute_unit)
        state_layout.addRow(self._strings.settings_walk_duration + " (min)", self._walk_min_spin)

        self._walk_max_spin = QSpinBox()
        self._walk_max_spin.setRange(1, 60)
        self._walk_max_spin.setValue(int(self._settings.walk_duration_maximum / 60))
        self._walk_max_spin.setSuffix(" " + self._strings.minute_unit)
        state_layout.addRow(self._strings.settings_walk_duration + " (max)", self._walk_max_spin)

        self._walk_speed_spin = QSpinBox()
        self._walk_speed_spin.setRange(1, 200)
        self._walk_speed_spin.setValue(int(self._settings.walk_base_speed))
        state_layout.addRow(self._strings.settings_walk_speed, self._walk_speed_spin)

        tabs.addTab(state_tab, self._strings.settings_state_section)

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(self._strings.settings_save)
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton(self._strings.cancel)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _save(self):
        lang = self._lang_combo.currentData()
        self._result_settings = AppSettings(
            language=lang,
            cat_name=self._cat_name_edit.text(),
            user_salutation=self._salutation_edit.text(),
            selected_asset_pack_id=self._settings.selected_asset_pack_id,
            reminders_enabled=self._reminder_enabled_check.isChecked(),
            water_reminder_interval=self._water_interval_spin.value() * 60,
            water_reminder_message_suffix=self._water_msg_edit.text(),
            movement_reminder_interval=self._move_interval_spin.value() * 60,
            movement_reminder_message_suffix=self._move_msg_edit.text(),
            custom_reminder_enabled=False,
            custom_reminder_interval=1800,
            custom_reminder_message_suffix="休息一下吧",
            outing_departure_message_suffix=self._outing_msg_edit.text(),
            default_outing_duration=self._outing_duration_spin.value() * 60,
            rest_duration_minimum=self._rest_min_spin.value() * 60,
            rest_duration_maximum=self._rest_max_spin.value() * 60,
            walk_duration_minimum=self._walk_min_spin.value() * 60,
            walk_duration_maximum=self._walk_max_spin.value() * 60,
            walk_base_speed=self._walk_speed_spin.value(),
            cat_scale_percent=self._scale_spin.value(),
            start_position_percent=self._start_pos_spin.value(),
            cat_activity_scope=self._scope_combo.currentData(),
        )
        self.accept()
