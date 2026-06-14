from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class OutingCollectable:
    id: str
    chinese_name: str
    english_name: str
    image_file: str = ""
    rarity: str = "1"
    author: str = ""

    @classmethod
    def from_json(cls, data: dict) -> "OutingCollectable":
        return cls(
            id=data["id"],
            chinese_name=data["chinese_name"],
            english_name=data["english_name"],
            image_file=data.get("image_path", f"collectables/{data['id']}.png"),
            rarity=str(data.get("rarity", "1")),
            author=data.get("author", ""),
        )


@dataclass
class OutingEvent:
    id: str
    chinese_description: str
    english_description: str
    event_type: str = ""
    author: str = ""

    @classmethod
    def from_json(cls, data: dict) -> "OutingEvent":
        return cls(
            id=data["id"],
            chinese_description=data["chinese_description"],
            english_description=data["english_description"],
            event_type=data.get("event_type", ""),
            author=data.get("author", ""),
        )


@dataclass
class OutingCatalog:
    collectables: list[OutingCollectable] = None
    events: list[OutingEvent] = None

    @property
    def empty(self) -> bool:
        return not self.collectables and not self.events


class OutingRewardGenerator:
    def __init__(self, catalog: OutingCatalog):
        self._catalog = catalog

    def reward(self, outing_duration: float) -> Optional["OutingReward"]:
        # More likely to get a reward with longer outing
        probability = min(0.8, 0.3 + outing_duration / (60 * 60) * 0.3)
        if random.random() > probability:
            return None
        if self._catalog.collectables and random.random() < 0.7:
            collectable = random.choice(self._catalog.collectables)
            return OutingReward.collectable(collectable)
        if self._catalog.events:
            event = random.choice(self._catalog.events)
            return OutingReward.event(event)
        return None

    def event_reward(self) -> Optional["OutingReward"]:
        if self._catalog.events:
            event = random.choice(self._catalog.events)
            return OutingReward.event(event)
        return None


class OutingReward:
    def __init__(self, kind: str, collectable: Optional[OutingCollectable] = None, event: Optional[OutingEvent] = None):
        self.kind = kind
        self.collectable = collectable
        self.event = event

    @classmethod
    def collectable(cls, c: OutingCollectable) -> "OutingReward":
        return cls("collectable", collectable=c)

    @classmethod
    def event(cls, e: OutingEvent) -> "OutingReward":
        return cls("event", event=e)


class OutingCatalogLoader:
    def __init__(self, resources_dir: Optional[str] = None):
        if resources_dir is None:
            self._resources_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "resources", "Outing"
            )
        else:
            self._resources_dir = resources_dir

    def load_catalog(self) -> OutingCatalog:
        collectables = self._load_collectables()
        events = self._load_events()
        return OutingCatalog(collectables=collectables, events=events)

    def image_url(self, collectable: OutingCollectable) -> str:
        return os.path.join(self._resources_dir, "collectables", collectable.image_file)

    def _load_collectables(self) -> list[OutingCollectable]:
        path = os.path.join(self._resources_dir, "collectables.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [OutingCollectable.from_json(item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _load_events(self) -> list[OutingEvent]:
        path = os.path.join(self._resources_dir, "events.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [OutingEvent.from_json(item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []


class CollectableInventory:
    def __init__(self):
        self._collectable_ids: set[str] = set()
        self.recent_new_collectable_id: Optional[str] = None

    @property
    def collectable_ids(self) -> set[str]:
        return self._collectable_ids

    @classmethod
    def from_ids(cls, ids: list[str]) -> "CollectableInventory":
        inv = cls()
        inv._collectable_ids = set(ids)
        return inv

    def record_collectable(self, collectable_id: str) -> bool:
        if collectable_id in self._collectable_ids:
            return False
        self._collectable_ids.add(collectable_id)
        self.recent_new_collectable_id = collectable_id
        return True

    def clear_recent_new_marker(self):
        self.recent_new_collectable_id = None

    def has_collectable(self, collectable_id: str) -> bool:
        return collectable_id in self._collectable_ids

    def to_list(self) -> list[str]:
        return sorted(self._collectable_ids)

    @classmethod
    def empty(cls) -> "CollectableInventory":
        return cls()
