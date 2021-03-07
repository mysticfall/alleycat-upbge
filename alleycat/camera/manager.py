from collections import OrderedDict
from itertools import chain
from typing import Callable, Final, Sequence, Type

import rx
from alleycat.reactive import RV, functions as rv
from bge.types import KX_GameObject
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from returns.iterables import Fold
from returns.maybe import Maybe, Nothing, Some
from returns.result import ResultE, Success
from rx import Observable, operators as ops

from alleycat.camera import CameraControl, FirstPersonCamera, ThirdPersonCamera
from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.control import TurretControl, ZoomControl
from alleycat.game import GameContext
from alleycat.input import InputMap


class CameraManager(ActivatableComponent[KX_GameObject]):
    class ArgKeys(ActivatableComponent.ArgKeys):
        ROTATION_INPUT: Final = "Rotation Input"
        ROTATION_SENSITIVITY: Final = "Rotation Sensitivity"
        ZOOM_INPUT: Final = "Zoom Input"
        ZOOM_SENSITIVITY: Final = "Zoom Sensitivity"

    args = OrderedDict(chain(ActivatableComponent.args.items(), (
        (ArgKeys.ROTATION_INPUT, "view/rotate"),
        (ArgKeys.ROTATION_SENSITIVITY, 1.0),
        (ArgKeys.ZOOM_INPUT, "view/zoom"),
        (ArgKeys.ZOOM_SENSITIVITY, 1.0)
    )))

    cameras: RV[Sequence[CameraControl]] = rv.new_view()

    first_person_camera: RV[Maybe[FirstPersonCamera]] = cameras.map(
        lambda _, cameras: next((Some(c) for c in cameras if isinstance(c, FirstPersonCamera)), Nothing))

    third_person_camera: RV[Maybe[FirstPersonCamera]] = cameras.map(
        lambda _, cameras: next((Some(c) for c in cameras if isinstance(c, ThirdPersonCamera)), Nothing))

    active_camera: RV[Maybe[CameraControl]] = cameras.pipe(lambda o: (
        ops.map(lambda cameras: map(lambda c: rv.observe(c.active).pipe(
            ops.do_action(
                lambda a: next(map(lambda v: v.deactivate(), filter(lambda v: v != c, cameras)), None) if a else None),
            ops.map(lambda a: (a, c))), cameras)),
        ops.map(lambda i: rx.combine_latest(*i).pipe(
            ops.map(lambda v: next((Some(c[1]) for c in v if c[0]), Nothing)))),
        ops.switch_latest(),
        ops.distinct_until_changed(),
        ops.do_action(lambda c: o.logger.info("Switching camera mode to %s.", c))
    ))

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

    @inject
    def start(self, args: dict, input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        assert args
        assert input_map

        super().start(args)

        # noinspection PyTypeChecker
        cameras = tuple(filter(lambda c: isinstance(c, CameraControl), self.object.components))

        # noinspection PyTypeChecker
        self.cameras = rx.return_value(cameras)

        self.logger.info("Found camera controls: %s.", cameras)

        props = ArgumentReader(args)

        active_camera = rv.observe(self.active_camera).pipe(
            ops.map(lambda camera: camera.map(lambda c: rx.return_value(c)).or_else_call(rx.empty)),
            ops.switch_latest(),
            ops.distinct_until_changed())

        def read_input(key_input: str, key_sensitivity: str) -> ResultE[Observable]:
            # noinspection PyShadowingBuiltins
            input = props.require(key_input, str)
            sensitivity = props.read(key_sensitivity, float).value_or(1.0)

            self.logger.debug("args['%s'] = %s", key_input, input)
            self.logger.debug("args['%s'] = %s", key_sensitivity, sensitivity)

            # noinspection PyTypeChecker
            return input \
                .map(lambda s: s.split("/")) \
                .bind(input_map.observe) \
                .map(lambda o: o.pipe(ops.map(lambda v: v * sensitivity)))

        def rotate(control: TurretControl, value: Vector):
            control.pitch += value.y
            control.yaw += value.x

        def zoom(control: ZoomControl, value: float):
            control.distance = max(control.distance - value * 0.1, 0)

        def setup_input(events: Observable, valid_type: Type, handler: Callable):
            active_camera.pipe(
                ops.filter(lambda c: isinstance(c, valid_type)),
                ops.map(lambda c: events.pipe(ops.map(lambda v: (c, v)))),
                ops.switch_latest(),
                ops.filter(lambda _: self.active),
                ops.take_until(self.on_dispose)
            ).subscribe(lambda v: handler(v[0], v[1]), on_error=self.error_handler)

        def setup_switcher(events: Observable):
            first_person_camera = active_camera.pipe(ops.filter(lambda c: isinstance(c, FirstPersonCamera)))
            third_person_camera = active_camera.pipe(ops.filter(lambda c: isinstance(c, ThirdPersonCamera)))

            first_person_camera.pipe(
                ops.map(lambda c: events.pipe(
                    ops.filter(lambda v: v < 0),
                    ops.take(1)
                )),
                ops.switch_latest(),
                ops.filter(lambda _: self.active),
                ops.take_until(self.on_dispose)
            ).subscribe(lambda _: self.switch_to_3rd_person(), on_error=self.error_handler)

            third_person_camera.pipe(
                ops.map(lambda c: rv.observe(c.distance).pipe(
                    ops.filter(lambda v: v == 0),
                    ops.take(1))),
                ops.switch_latest(),
                ops.filter(lambda _: self.active),
                ops.take_until(self.on_dispose),
            ).subscribe(lambda _: self.switch_to_1st_person(), on_error=self.error_handler)

        rotation_input = read_input(self.ArgKeys.ROTATION_INPUT, self.ArgKeys.ROTATION_SENSITIVITY)
        zoom_input = read_input(self.ArgKeys.ZOOM_INPUT, self.ArgKeys.ZOOM_SENSITIVITY)

        rotation_setup = rotation_input.map(lambda i: setup_input(i, TurretControl, rotate))
        zoom_setup = zoom_input.map(lambda i: setup_input(i, ZoomControl, zoom))
        switcher_setup = zoom_input.map(setup_switcher)

        Fold.collect((rotation_setup, zoom_setup, switcher_setup), Success(())).alt(self.logger.warning)

    def switch_to_1st_person(self) -> None:
        self.first_person_camera.map(lambda c: c.activate())

    def switch_to_3rd_person(self) -> None:
        self.third_person_camera.map(lambda c: c.activate())
