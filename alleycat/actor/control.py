from collections import OrderedDict
from itertools import chain
from typing import Callable, Final, Mapping, Type

from alleycat.reactive import functions as rv
from bge.types import KX_GameObject
from bpy.types import Object
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from numpy import radians, sign
from returns.iterables import Fold
from returns.result import ResultE, Success, safe
from rx import Observable, operators as ops

from alleycat.actor import Character
from alleycat.camera import CameraManager, FirstPersonCamera, RotatableCamera, ThirdPersonCamera, ZoomableCamera
from alleycat.common import ArgumentReader, of_type
from alleycat.game import BaseComponent, GameContext, require_component
from alleycat.input import Axis2DBinding, AxisBinding, InputMap


class CharacterControl(BaseComponent[KX_GameObject]):
    class ArgKeys(BaseComponent.ArgKeys):
        CHARACTER: Final = "Character"
        CAMERA: Final = "Camera"
        MOVEMENT_INPUT: Final = "Movement Input"
        ROTATION_INPUT: Final = "Rotation Input"
        ZOOM_INPUT: Final = "Zoom Input"

    args = OrderedDict(chain(BaseComponent.args.items(), (
        (ArgKeys.CHARACTER, Object),
        (ArgKeys.CAMERA, Object),
        (ArgKeys.MOVEMENT_INPUT, "move"),
        (ArgKeys.ROTATION_INPUT, "view/rotate"),
        (ArgKeys.ZOOM_INPUT, "view/zoom")
    )))

    input_map: InputMap = Provide[GameContext.input.mappings]

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

    @property
    def character(self) -> Character:
        return self.params["character"]

    @property
    def camera_manager(self) -> CameraManager:
        return self.params["camera_manager"]

    @property
    def movement_input(self) -> Axis2DBinding:
        return self.params["movement_input"]

    @property
    def rotation_input(self) -> Axis2DBinding:
        return self.params["rotation_input"]

    @property
    def zoom_input(self) -> AxisBinding:
        return self.params["zoom_input"]

    @inject
    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        # noinspection PyTypeChecker
        character = args \
            .require(CharacterControl.ArgKeys.CHARACTER, Object) \
            .map(self.as_game_object) \
            .bind(lambda o: require_component(o, Character)) \
            .alt(lambda _: ValueError("Missing or invalid character object."))

        # noinspection PyTypeChecker
        camera_manager = args \
            .require(CharacterControl.ArgKeys.CAMERA, Object) \
            .map(self.as_game_object) \
            .bind(lambda o: require_component(o, CameraManager)) \
            .alt(lambda _: ValueError("Missing or invalid camera manager."))

        # noinspection PyTypeChecker
        movement_input = args \
            .require(CharacterControl.ArgKeys.MOVEMENT_INPUT, str) \
            .bind(self.input_map.require_binding) \
            .bind(safe(lambda b: of_type(b, Axis2DBinding)))

        # noinspection PyTypeChecker
        rotation_input = args \
            .require(CharacterControl.ArgKeys.ROTATION_INPUT, str) \
            .bind(self.input_map.require_binding) \
            .bind(safe(lambda b: of_type(b, Axis2DBinding)))

        # noinspection PyTypeChecker
        zoom_input = args \
            .require(CharacterControl.ArgKeys.ZOOM_INPUT, str) \
            .bind(self.input_map.require_binding) \
            .bind(safe(lambda b: of_type(b, AxisBinding)))

        result = Fold.collect((
            character.map(lambda c: ("character", c)),
            camera_manager.map(lambda c: ("camera_manager", c)),
            movement_input.map(lambda i: ("movement_input", i)),
            rotation_input.map(lambda i: ("rotation_input", i)),
            zoom_input.map(lambda i: ("zoom_input", i))
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        def move(value: Vector):
            if self.character.initialized and self.character.locomotion.initialized:
                self.character.locomotion.movement = value

        rv \
            .observe(self.movement_input.value) \
            .pipe(ops.filter(lambda _: self.active), ops.take_until(self.on_dispose)) \
            .subscribe(move, on_error=self.error_handler)

        active_camera = rv.observe(self.camera_manager.active_camera)

        def rotate(control: RotatableCamera, value: Vector):
            control.pitch += value.y
            control.yaw += value.x

        def zoom(control: ZoomableCamera, value: float):
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
            ).subscribe(lambda _: self.camera_manager.switch_to_3rd_person(), on_error=self.error_handler)

            third_person_camera.pipe(
                ops.map(lambda c: rv.observe(c.distance).pipe(
                    ops.filter(lambda v: v <= c.min_distance),
                    ops.take(1))),
                ops.switch_latest(),
                ops.filter(lambda _: self.active),
                ops.take_until(self.on_dispose),
            ).subscribe(lambda _: self.camera_manager.switch_to_1st_person(), on_error=self.error_handler)

        on_rotate = rv.observe(self.rotation_input.value)
        on_zoom = rv.observe(self.zoom_input.value)

        setup_input(on_rotate, RotatableCamera, rotate)
        setup_input(on_zoom, ZoomableCamera, zoom)

        setup_switcher(on_zoom)

    def process(self) -> None:
        view = self.camera_manager.active_camera

        angle = sign(view.yaw) * min(radians(3), abs(view.yaw)) * self.character.locomotion.movement.length_squared

        view.yaw -= angle
        self.character.object.applyRotation(Vector((0, 0, -angle)), True)
