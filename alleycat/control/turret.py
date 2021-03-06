import math
from abc import ABC
from collections import OrderedDict
from typing import Final

from alleycat.reactive import RP, RV, functions as rv
from dependency_injector.wiring import Provide, inject
from mathutils import Euler, Vector
from rx import operators as ops

from alleycat.common import ArgumentReader, BaseComponent
from alleycat.game import GameContext
from alleycat.input import InputMap
from alleycat.math import clamp, normalize_angle


class TurretControl(BaseComponent, ABC):
    class ArgKeys:
        ROTATION_INPUT: Final = "Rotation Input"
        ROTATION_SENSITIVITY: Final = "Rotation Sensitivity"

    args = OrderedDict((
        (ArgKeys.ROTATION_INPUT, "view/rotate"),
        (ArgKeys.ROTATION_SENSITIVITY, 1.0)
    ))

    pitch: RP[float] = rv.from_value(0.0).validate(lambda _, v: clamp(v, -math.pi / 2, math.pi / 2))

    yaw: RP[float] = rv.from_value(0.0).validate(lambda _, v: normalize_angle(v))

    # noinspection PyArgumentList
    rotation: RV[Euler] = rv.combine_latest(pitch, yaw)(ops.map(lambda v: Euler((v[0], 0, -v[1]), "XYZ")))

    @inject
    def start(
            self,
            args: dict,
            input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        props = ArgumentReader(args)

        sensitivity = props.read(self.ArgKeys.ROTATION_SENSITIVITY, float).value_or(1.0)

        def rotate(value: Vector):
            self.pitch += value.y * sensitivity
            self.yaw += value.x * sensitivity

        props.require(self.ArgKeys.ROTATION_INPUT, str) \
            .map(lambda s: s.split("/")) \
            .bind(input_map.observe) \
            .map(lambda o: o.subscribe(rotate, on_error=self.error_handler)) \
            .alt(self.logger.warning)
