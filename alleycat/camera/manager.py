from functools import cached_property
from itertools import chain
from typing import Mapping, NamedTuple, Sequence

import rx
from alleycat.reactive import RV, functions as rv
from bge.types import KX_GameObject
from dependency_injector.wiring import Provide
from returns.curry import partial
from returns.iterables import Fold
from returns.maybe import Maybe, Nothing, Some
from returns.result import ResultE, Success, safe
from rx import operators as ops
from rx.subject import Subject
from validator_collection import iterable

from alleycat.camera import CameraControl, FirstPersonCamera, ThirdPersonCamera
from alleycat.common import ArgumentReader
from alleycat.game import BaseComponent, GameContext
from alleycat.input import InputMap


class CameraState(NamedTuple):
    camera: CameraControl
    active: bool


class CameraManager(BaseComponent[KX_GameObject]):
    active_camera: RV[CameraControl] = rv.new_view()

    input_map: InputMap = Provide[GameContext.input.mappings]

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

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        # noinspection PyTypeChecker
        cameras = Success(filter(lambda c: isinstance(c, CameraControl), self.object.components)) \
            .bind(safe(lambda c: tuple(iterable(c)))) \
            .alt(lambda _: ValueError("No camera control found."))

        result = Fold.collect((
            cameras.map(lambda c: ("cameras", c)),
        ), Success(())).map(chain).map(dict)  # type:ignore

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
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

        super().initialize()

    def switch_to_1st_person(self) -> None:
        self.first_person_camera.map(lambda c: c.activate())

    def switch_to_3rd_person(self) -> None:
        self.third_person_camera.map(lambda c: c.activate())
