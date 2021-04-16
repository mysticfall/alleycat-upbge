from collections import OrderedDict
from functools import cached_property
from itertools import chain
from typing import Callable, Final, Mapping, NamedTuple, Sequence, Type

import rx
from alleycat.reactive import RV, functions as rv
from bge.types import KX_GameObject
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from returns.curry import partial
from returns.iterables import Fold
from returns.maybe import Maybe, Nothing, Some
from returns.result import ResultE, Success, safe
from rx import Observable, operators as ops
from rx.subject import Subject
from validator_collection import iterable

from alleycat.camera import CameraControl, FirstPersonCamera, ThirdPersonCamera
from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.control import TurretControl, ZoomControl
from alleycat.game import GameContext
from alleycat.input import InputMap


class CameraState(NamedTuple):
    camera: CameraControl
    active: bool


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

    active_camera: RV[CameraControl] = rv.new_view()

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

        self._active_camera = Subject()

    @property
    def cameras(self) -> Sequence[CameraControl]:
        return self.params["cameras"]

    @cached_property
    def first_person_camera(self) -> Maybe[FirstPersonCamera]:
        return next((Some(c) for c in self.cameras if isinstance(c, FirstPersonCamera)), Nothing)

    @cached_property
    def third_person_camera(self) -> Maybe[ThirdPersonCamera]:
        return next((Some(c) for c in self.cameras if isinstance(c, ThirdPersonCamera)), Nothing)

    @inject
    def init_params(
            self,
            args: ArgumentReader,
            input_map: InputMap = Provide[GameContext.input.mappings]) -> ResultE[Mapping]:
        def read_input(key_input: str, key_sensitivity: str) -> ResultE[Observable]:
            # noinspection PyShadowingBuiltins
            input = args.require(key_input, str).alt(lambda _: ValueError(f"Missing input key: '%s'." % key_input))
            sensitivity = args.read(key_sensitivity, float).value_or(1.0)

            # noinspection PyTypeChecker
            return input \
                .map(lambda s: s.split("/")) \
                .bind(input_map.observe) \
                .map(lambda o: o.pipe(ops.map(lambda v: v * sensitivity)))

        # noinspection PyTypeChecker
        cameras = Success(filter(lambda c: isinstance(c, CameraControl), self.object.components)) \
            .bind(safe(lambda c: tuple(iterable(c)))) \
            .alt(lambda _: ValueError("No camera control found."))

        rotation_input = read_input(self.ArgKeys.ROTATION_INPUT, self.ArgKeys.ROTATION_SENSITIVITY)
        zoom_input = read_input(self.ArgKeys.ZOOM_INPUT, self.ArgKeys.ZOOM_SENSITIVITY)

        result = Fold.collect((
            cameras.map(lambda c: ("cameras", c)),
            rotation_input.map(lambda i: ("rotation_input", i)),
            zoom_input.map(lambda i: ("zoom_input", i))
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        def deactivate_others(current: CameraControl, active: CameraControl):
            next(map(lambda c: c.deactivate(), filter(lambda c: c != current, self.cameras)), None) if active else None

        try:
            next(filter(lambda c: c.active, self.cameras))
        except StopIteration:
            next(iter(self.cameras)).activate()

        camera_states = map(lambda c: rv.observe(c.active).pipe(
            ops.do_action(partial(deactivate_others, c)),
            ops.map(lambda state: CameraState(c, state))), self.cameras)

        # noinspection PyTypeChecker
        self.active_camera = rx.combine_latest(*camera_states).pipe(
            ops.map(lambda states: next(s.camera for s in states if s.active)),
            ops.distinct_until_changed(),
            ops.do_action(lambda c: self.logger.info("Switching camera mode to %s.", c)))

        active_camera = rv.observe(self.active_camera)

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
            ).subscribe(lambda v: handler(*v), on_error=self.error_handler)

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

        rotation_input = self.params["rotation_input"]
        zoom_input = self.params["zoom_input"]

        setup_input(rotation_input, TurretControl, rotate)
        setup_input(zoom_input, ZoomControl, zoom)

        setup_switcher(zoom_input)

    def switch_to_1st_person(self) -> None:
        self.first_person_camera.map(lambda c: c.activate())

    def switch_to_3rd_person(self) -> None:
        self.third_person_camera.map(lambda c: c.activate())
