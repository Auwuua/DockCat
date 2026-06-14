from __future__ import annotations

import random
import time
from typing import Callable, Optional

from .state import (
    CatState,
    LongDurationState,
    OutingPhase,
    ReminderType,
    dialogue,
    dragged,
    outing,
    resting,
    transitioning,
    walking,
    walking,
)

RandomDuration = Callable[[tuple[float, float]], float]


class CatStateMachine:
    def __init__(
        self,
        initial_position: tuple[float, float] = (0, 0),
        entrance_provider: Optional[Callable[[], tuple[float, float]]] = None,
        walking_duration_range: tuple[float, float] = (120, 300),
        resting_duration_range: tuple[float, float] = (120, 300),
        random_duration: Optional[RandomDuration] = None,
        random_long_duration_state: Optional[Callable[[], LongDurationState]] = None,
        random_transition_insertion: Optional[Callable[[], bool]] = None,
    ):
        self._state: CatState = resting()
        self._position: tuple[float, float] = initial_position
        self._entrance_provider = entrance_provider or (lambda: initial_position)
        self._random_duration = random_duration or self._default_random_duration
        self._random_long_duration_state = (
            random_long_duration_state
            or (lambda: random.choice(list(LongDurationState)))
        )
        self._random_transition_insertion = (
            random_transition_insertion or (lambda: random.random() < 1.0 / 3.0)
        )
        self._walking_duration_range = walking_duration_range
        self._resting_duration_range = resting_duration_range

        self.on_transition: Optional[Callable[[CatState, CatState], None]] = None
        self.on_duration_scheduled: Optional[Callable[[CatState, float], None]] = None
        self.on_reminder_deferred: Optional[Callable[[ReminderType], None]] = None

    @property
    def state(self) -> CatState:
        return self._state

    @property
    def position(self) -> tuple[float, float]:
        return self._position

    @position.setter
    def position(self, pos: tuple[float, float]):
        self._position = pos

    def update_parameters(self, walking_duration_range: tuple[float, float], resting_duration_range: tuple[float, float]):
        self._walking_duration_range = walking_duration_range
        self._resting_duration_range = resting_duration_range

    def start(self):
        self._position = self._entrance_provider()
        self._enter_transitioning()

    def enter_random_long_duration_state(self):
        ls = self._random_long_duration_state()
        if ls == LongDurationState.WALKING:
            self._transition_to(walking())
            self._schedule_current_state()
        else:
            self._transition_to(resting())
            self._schedule_current_state()

    def finish_transitioning(self):
        if self._state.name != "transitioning":
            return
        self.enter_random_long_duration_state()

    def finish_scheduled_state(self, scheduled_state: CatState):
        if self._state != scheduled_state:
            return
        if scheduled_state.name in ("transitioning",):
            self.finish_transitioning()
        elif scheduled_state.name in ("resting", "walking"):
            self._enter_random_long_duration_state_with_optional_transition()

    def begin_drag(self):
        if not self._state.can_begin_drag:
            return
        self._transition_to(dragged())

    def update_drag_position(self, point: tuple[float, float]):
        if self._state.name != "dragged":
            return
        self._position = point

    def update_long_duration_position(self, point: tuple[float, float]):
        if not self._state.is_long_duration:
            return
        self._position = point

    def update_visible_position(self, point: tuple[float, float]):
        allowed = ("transitioning", "walking", "resting", "dragged", "dialogue")
        if self._state.name in allowed:
            self._position = point
        elif self._state.name == "outing" and self._state.params.get("phase") in (
            OutingPhase.ASKING, OutingPhase.CONFIRMING_DEPARTURE, OutingPhase.RETURNED
        ):
            self._position = point

    def update_outing_walk_position(self, point: tuple[float, float]):
        if self._state.name == "outing" and self._state.params.get("phase") in (
            OutingPhase.LEAVING, OutingPhase.RETURNING
        ):
            self._position = point

    def end_drag(self, at_point: tuple[float, float]):
        if self._state.name != "dragged":
            return
        self._position = at_point
        self._enter_random_long_duration_state_with_optional_transition()

    def request_reminder(self, type_: ReminderType) -> bool:
        if self._state.is_long_duration:
            self._transition_to(dialogue(type_))
            return True
        else:
            if self.on_reminder_deferred:
                self.on_reminder_deferred(type_)
            return False

    def finish_reminder(self):
        if self._state.name != "dialogue":
            return
        self.enter_random_long_duration_state()

    def begin_outing_prompt(self):
        if self._state.is_outing:
            return
        self._transition_to(outing(OutingPhase.ASKING))

    def confirm_outing(self):
        if not (self._state.name == "outing" and self._state.params.get("phase") == OutingPhase.ASKING):
            return
        self._transition_to(outing(OutingPhase.CONFIRMING_DEPARTURE))

    def depart_outing(self):
        if not (self._state.name == "outing" and self._state.params.get("phase") == OutingPhase.CONFIRMING_DEPARTURE):
            return
        self._transition_to(outing(OutingPhase.LEAVING))

    def restore_outing_away(self):
        self._transition_to(outing(OutingPhase.AWAY))

    def mark_away(self):
        if not (self._state.name == "outing" and self._state.params.get("phase") == OutingPhase.LEAVING):
            return
        self._transition_to(outing(OutingPhase.AWAY))

    def return_from_outing(self):
        if self._state.name != "outing":
            return
        self._position = self._entrance_provider()
        self._transition_to(outing(OutingPhase.RETURNING))

    def finish_return_walk(self):
        if not (self._state.name == "outing" and self._state.params.get("phase") == OutingPhase.RETURNING):
            return
        self._transition_to(outing(OutingPhase.RETURNED))

    def welcome_back(self):
        if not (self._state.name == "outing" and self._state.params.get("phase") == OutingPhase.RETURNED):
            return
        self._enter_random_long_duration_state_with_optional_transition()

    @property
    def is_outing(self) -> bool:
        return self._state.name == "outing"

    def _schedule_current_state(self):
        if self._state.name == "walking":
            duration = self._random_duration(self._walking_duration_range)
        elif self._state.name == "resting":
            duration = self._random_duration(self._resting_duration_range)
        else:
            return
        if self.on_duration_scheduled:
            self.on_duration_scheduled(self._state, duration)

    def _enter_random_long_duration_state_with_optional_transition(self):
        if self._random_transition_insertion():
            self._enter_transitioning()
        else:
            self.enter_random_long_duration_state()

    def _enter_transitioning(self):
        self._transition_to(transitioning())
        if self.on_duration_scheduled:
            self.on_duration_scheduled(transitioning(), 2.0)

    def _transition_to(self, new_state: CatState):
        old_state = self._state
        self._state = new_state
        print(f"State: {old_state} -> {new_state}")
        if self.on_transition:
            self.on_transition(old_state, new_state)

    @staticmethod
    def _default_random_duration(range_: tuple[float, float]) -> float:
        lower = int((range_[0] / 60 + 0.5))
        upper = int((range_[1] / 60))
        if lower > upper:
            return range_[0]
        return float(random.randint(lower, upper) * 60)
