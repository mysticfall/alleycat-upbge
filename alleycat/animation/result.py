from __future__ import annotations

from mathutils import Vector
from validator_collection import not_empty


class AnimationResult:
    __slots__ = ["_offset"]

    def __init__(self) -> None:
        self._offset = Vector((0, 0, 0))

    @property
    def offset(self) -> Vector:
        return self._offset

    @offset.setter
    def offset(self, value: Vector) -> None:
        v = not_empty(value)

        self._offset.x = v.x
        self._offset.y = v.y
        self._offset.z = v.z

    def copy(self, other: AnimationResult) -> AnimationResult:
        self.offset = not_empty(other).offset

        return other

    def reset(self) -> None:
        self._offset.x = 0
        self._offset.y = 0
        self._offset.z = 0
