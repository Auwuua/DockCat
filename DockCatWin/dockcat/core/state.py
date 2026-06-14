from enum import Enum, auto
from typing import Optional


class CatActivityScope(str, Enum):
    DOCK_EDGE = "dockEdge"
    DESKTOP = "desktop"


class AppLanguage(str, Enum):
    CHINESE = "chinese"
    ENGLISH = "english"


class ReminderType(str, Enum):
    WATER = "water"
    MOVEMENT = "movement"
    CUSTOM = "custom"


class OutingPhase(str, Enum):
    ASKING = "asking"
    CONFIRMING_DEPARTURE = "confirmingDeparture"
    LEAVING = "leaving"
    AWAY = "away"
    RETURNING = "returning"
    RETURNED = "returned"


class CatState:
    """Represents cat states - uses tagged union pattern matching state name."""

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.params = kwargs

    @property
    def is_long_duration(self) -> bool:
        return self.name in ("walking", "resting")

    @property
    def is_outing(self) -> bool:
        return self.name == "outing"

    @property
    def can_begin_drag(self) -> bool:
        return self.name in ("walking", "resting", "transitioning")

    def __eq__(self, other):
        if isinstance(other, CatState):
            return self.name == other.name and self.params == other.params
        return NotImplemented

    def __repr__(self):
        if self.name == "outing":
            return f"CatState({self.name}, {self.params.get('phase')})"
        if self.name == "dialogue":
            return f"CatState({self.name}, {self.params.get('type')})"
        return f"CatState({self.name})"


# Factory functions for states
def transitioning():
    return CatState("transitioning")


def walking():
    return CatState("walking")


def resting():
    return CatState("resting")


def dragged():
    return CatState("dragged")


def dialogue(reminder_type: ReminderType):
    return CatState("dialogue", type=reminder_type)


def outing(phase: OutingPhase):
    return CatState("outing", phase=phase)


class LongDurationState(Enum):
    WALKING = "walking"
    RESTING = "resting"
