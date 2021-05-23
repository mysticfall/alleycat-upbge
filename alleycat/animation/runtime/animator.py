from typing import Optional

import bpy
from bge.types import KX_GameObject
from bpy.types import Action
from returns.maybe import Maybe
from validator_collection import not_empty

from alleycat.animation import Animator, BlendMode, PlayMode


class GameObjectAnimator(Animator):
    __slots__ = ["_target"]

    def __init__(
            self,
            target: KX_GameObject,
            time_delta: float = 0,
            layer: int = 10000,
            weight: float = 1.0,
            speed: float = 1.0,
            priority: int = 0,
            blend: float = 0.0,
            play_mode: PlayMode = PlayMode.Play,
            blend_mode: BlendMode = BlendMode.Blend,
            root_bone: Optional[str] = None) -> None:
        self._target = not_empty(target)

        super().__init__(time_delta, layer, weight, speed, priority, blend, play_mode, blend_mode, root_bone)

    @property
    def target(self) -> KX_GameObject:
        return self._target

    def play(self,
             action: Action,
             start_frame: Optional[float] = None,
             end_frame: Optional[float] = None) -> None:
        self.target.playAction(
            name=not_empty(action).name,
            start_frame=Maybe.from_optional(start_frame).value_or(0.0),
            end_frame=Maybe.from_optional(end_frame).value_or(action.frame_range[-1]),
            layer=self.layer,
            priority=self.priority,
            blendin=self.blend,
            play_mode=self.play_mode.value,
            layer_weight=self.weight,
            speed=self.speed,
            blend_mode=self.blend_mode.value)

    def stop(self):
        self.target.stopAction(self.layer)

    @property
    def action(self) -> Maybe[Action]:
        return Maybe.from_optional(self.target.getActionName(self.layer)).map(bpy.data.actions.get)

    @property
    def frame(self) -> float:
        return self.target.getActionFrame(self.layer)

    @frame.setter
    def frame(self, value: float) -> None:
        self.target.setActionFrame(self.layer, value)

    @property
    def playing(self) -> bool:
        return self.target.isPlayingAction(self.layer)
