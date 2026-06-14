from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AssetManifest:
    id: str
    name: str
    author: str
    canvas_width: int
    canvas_height: int
    default_anchor: tuple[float, float]
    poses: dict = field(default_factory=lambda: {
        "resting": "poses/resting",
        "held": "poses/held",
        "dialogue": "poses/dialogue",
        "transition": "poses/transition",
    })
    animations: dict = field(default_factory=lambda: {
        "walk": {"fps": 3, "frames": []}
    })
    app_icons: Optional[dict] = None

    @classmethod
    def from_dict(cls, data: dict) -> "AssetManifest":
        poses = data.get("poses", {})
        if isinstance(poses, dict):
            # Legacy: might have "stand" and "stretch"
            resolved_poses = {
                "resting": poses.get("resting", "poses/resting"),
                "held": poses.get("held", "poses/held"),
                "dialogue": poses.get("dialogue", poses.get("stand", "poses/dialogue")),
                "transition": poses.get("transition", poses.get("stretch", "poses/transition")),
            }
        else:
            resolved_poses = {"resting": "poses/resting", "held": "poses/held", "dialogue": "poses/dialogue", "transition": "poses/transition"}
        anims = data.get("animations", {})
        if isinstance(anims, dict):
            walk = anims.get("walk", {"fps": 3, "frames": []})
        else:
            walk = {"fps": 3, "frames": []}
        anchor = data.get("default_anchor", {"x": 0.5, "y": 0.88})
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            author=data.get("author", ""),
            canvas_width=data.get("canvas_width", 1280),
            canvas_height=data.get("canvas_height", 1280),
            default_anchor=(anchor["x"], anchor["y"]),
            poses=resolved_poses,
            animations={"walk": walk},
            app_icons=data.get("app_icons"),
        )


class CatAssetPack:
    def __init__(self, manifest: AssetManifest, root_url: str):
        self.manifest = manifest
        self.root_url = root_url

    @property
    def id(self) -> str:
        folder_name = os.path.basename(self.root_url)
        return self.manifest.id if folder_name == "DefaultCat" else folder_name

    @property
    def resting_poses_dir(self) -> str:
        return os.path.join(self.root_url, self.manifest.poses["resting"])

    @property
    def held_poses_dir(self) -> str:
        return os.path.join(self.root_url, self.manifest.poses["held"])

    @property
    def dialogue_poses_dir(self) -> str:
        return os.path.join(self.root_url, self.manifest.poses["dialogue"])

    @property
    def transition_poses_dir(self) -> str:
        return os.path.join(self.root_url, self.manifest.poses["transition"])

    @property
    def walk_animation_dir(self) -> str:
        return os.path.join(self.root_url, "animations", "walk")

    @property
    def sleep_icon_url(self) -> Optional[str]:
        icons = self.manifest.app_icons
        if icons and "sleep" in icons:
            return os.path.join(self.root_url, icons["sleep"])
        return None

    @property
    def empty_icon_url(self) -> Optional[str]:
        icons = self.manifest.app_icons
        if icons and "empty" in icons:
            return os.path.join(self.root_url, icons["empty"])
        return None

    def url_for(self, relative_path: str) -> str:
        return os.path.join(self.root_url, relative_path)


class AssetPackLoader:
    def __init__(self, packs_dir: str = None, default_dir: str = None):
        if packs_dir is None:
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "CatPacks")
        else:
            base = packs_dir
        self._base_dir = base
        if default_dir is None:
            self._default_pack_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "DefaultCat")
        else:
            self._default_pack_dir = default_dir

    def load_default_pack(self) -> Optional[CatAssetPack]:
        manifest_path = os.path.join(self._default_pack_dir, "manifest.json")
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            manifest = AssetManifest.from_dict(data)
            return CatAssetPack(manifest, self._default_pack_dir)
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Failed to load default pack: {e}")
            return None

    def load_selected_pack(self, selected_id: str) -> Optional[CatAssetPack]:
        if selected_id == "default-lizz":
            return self.load_default_pack()
        pack_dir = os.path.join(self._base_dir, selected_id)
        manifest_path = os.path.join(pack_dir, "manifest.json")
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            manifest = AssetManifest.from_dict(data)
            return CatAssetPack(manifest, pack_dir)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return self.load_default_pack()

    def custom_pack_ids(self) -> list[str]:
        if not os.path.isdir(self._base_dir):
            return []
        return [d for d in os.listdir(self._base_dir)
                if os.path.isdir(os.path.join(self._base_dir, d)) and d != "DefaultCat"]

    def custom_packs_root(self) -> str:
        return self._base_dir

    def prepare_custom_packs_directory(self):
        os.makedirs(self._base_dir, exist_ok=True)

    def validation_report(self, selected_id: str) -> dict:
        """Validate an asset pack and return a report."""
        pack = self.load_selected_pack(selected_id)
        if pack is None:
            return {"error": "资源包加载失败", "pack": None}
        pose_dirs = {
            "休息状态": pack.resting_poses_dir,
            "抱起状态": pack.held_poses_dir,
            "对话状态": pack.dialogue_poses_dir,
            "过渡状态": pack.transition_poses_dir,
        }
        pose_statuses = []
        for name, d in pose_dirs.items():
            files = [f for f in os.listdir(d) if f.lower().endswith((".png", ".jpg", ".jpeg"))] if os.path.isdir(d) else []
            pose_statuses.append({"name": name, "count": len(files), "ok": len(files) > 0})
        walk_files = [f for f in os.listdir(pack.walk_animation_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))] if os.path.isdir(pack.walk_animation_dir) else []
        return {
            "pack": pack,
            "pose_statuses": pose_statuses,
            "walk_frame_count": len(walk_files),
            "error": None,
        }
