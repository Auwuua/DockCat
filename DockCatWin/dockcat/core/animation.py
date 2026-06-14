from __future__ import annotations

import os
import random
from typing import Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap

from .assets import CatAssetPack


class SpriteAnimation:
    def __init__(self, frames: list[QPixmap], fps: float, loops: bool = True):
        self.frames = frames
        self.fps = fps
        self.loops = loops

    @property
    def frame_duration(self) -> float:
        return 1.0 / self.fps if self.fps > 0 else 1.0 / 6.0


class SpriteAnimator:
    def __init__(self):
        self._timer: Optional[QTimer] = None
        self._frame_index = 0

    def start(self, animation: SpriteAnimation, on_frame, on_finish=None):
        self.stop()
        self._frame_index = 0
        if not animation.frames:
            return
        on_frame(0)
        self._timer = QTimer()
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(lambda: self._tick(animation, on_frame, on_finish))
        self._timer.start(int(animation.frame_duration * 1000))

    def stop(self):
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._frame_index = 0

    def _tick(self, animation, on_frame, on_finish):
        self._frame_index += 1
        if self._frame_index >= len(animation.frames):
            if animation.loops:
                self._frame_index = 0
            else:
                self.stop()
                if on_finish:
                    on_finish()
                return
        on_frame(self._frame_index)


class PoseRenderer:
    def __init__(self, pack: CatAssetPack, fallback_pack: Optional[CatAssetPack] = None):
        self._pack = pack
        self._fallback_pack = fallback_pack

    def first_image(self, pose: str) -> Optional[QPixmap]:
        images = self._pose_images(pose)
        return images[0] if images else None

    def random_pose(self, pose: str, fallback: Optional[str] = None) -> tuple[Optional[QPixmap], bool]:
        images = self._pose_images(pose)
        if not images and fallback:
            images = self._pose_images(fallback)
        image = random.choice(images) if images else None
        return image, random.choice([True, False])

    def _pose_images(self, pose: str) -> list[QPixmap]:
        pack_images = self._pose_images_in_pack(pose, self._pack)
        if pack_images:
            return pack_images
        if self._fallback_pack:
            return self._pose_images_in_pack(pose, self._fallback_pack)
        return []

    def _pose_images_in_pack(self, pose: str, pack: CatAssetPack) -> list[QPixmap]:
        dir_map = {
            "resting": pack.resting_poses_dir,
            "held": pack.held_poses_dir,
            "dialogue": pack.dialogue_poses_dir,
            "transition": pack.transition_poses_dir,
        }
        dir_path = dir_map.get(pose)
        if not dir_path or not os.path.isdir(dir_path):
            return []
        files = sorted([
            f for f in os.listdir(dir_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])
        pixmaps = []
        for f in files:
            pix = QPixmap(os.path.join(dir_path, f))
            if not pix.isNull():
                pixmaps.append(pix)
        return pixmaps

    def animation_frames(self, anim_key: str = "walk") -> SpriteAnimation:
        fps = self._pack.manifest.animations.get(anim_key, {}).get("fps", 3)
        frames = self._walk_frames_from_dir(self._pack)
        if not frames and self._fallback_pack:
            frames = self._walk_frames_from_dir(self._fallback_pack)
        if not frames:
            first = self.first_image("dialogue")
            if first:
                frames = [first]
        return SpriteAnimation(frames, fps, loops=True)

    @staticmethod
    def _walk_frames_from_dir(pack: CatAssetPack) -> list[QPixmap]:
        dir_path = pack.walk_animation_dir
        if not os.path.isdir(dir_path):
            return []
        files = sorted([
            f for f in os.listdir(dir_path)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])
        pixmaps = []
        for f in files:
            pix = QPixmap(os.path.join(dir_path, f))
            if not pix.isNull():
                pixmaps.append(pix)
        return pixmaps

    def walk_animation_source_pack(self) -> Optional[CatAssetPack]:
        if self._walk_frames_from_dir(self._pack):
            return self._pack
        if self._fallback_pack and self._walk_frames_from_dir(self._fallback_pack):
            return self._fallback_pack
        return None
