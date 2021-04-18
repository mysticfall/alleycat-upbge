from abc import ABC
from collections import OrderedDict
from typing import Any, Final, Generic, Mapping, Type, TypeVar

from alleycat.reactive import RP, functions as rv
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import ID, Object
from returns.maybe import Maybe, Nothing
from returns.pipeline import is_successful
from returns.result import Result, ResultE, Success
from validator_collection import not_empty

from alleycat.common import ArgumentReader, IllegalStateError, Initializable
from alleycat.event import ComponentLoopSupport
from alleycat.game import Bootstrap
from alleycat.log import LoggingSupport

T = TypeVar("T", bound=KX_GameObject)
U = TypeVar("U", bound=ID)
V = TypeVar("V")
W = TypeVar("W", bound=KX_PythonComponent)


def find_component(obj: KX_GameObject, comp_type: Type[W]) -> Maybe[W]:
    try:
        return Maybe.from_value(next(filter(lambda c: isinstance(c, comp_type), not_empty(obj).components)))
    except StopIteration:
        return Nothing


def require_component(obj: KX_GameObject, comp_type: Type[W]) -> ResultE[W]:
    try:
        return Result.from_value(next(filter(lambda c: isinstance(c, comp_type), not_empty(obj).components)))
    except StopIteration:
        return Result.from_failure(ValueError(f"{obj} does not have any component of type {comp_type}."))


class NotStartedError(IllegalStateError):
    pass


class BaseComponent(Generic[T], ComponentLoopSupport, Initializable, LoggingSupport, KX_PythonComponent, ABC):
    class ArgKeys:
        ACTIVE: Final = "Active"

    args = OrderedDict((
        (ArgKeys.ACTIVE, True),
    ))

    object: T

    active: RP[bool] = rv.from_value(True)

    # noinspection PyUnusedLocal
    def __init__(self, obj: T):
        self._obj_name = obj.name
        self._params: ResultE[Mapping] = Result.from_failure(NotStartedError("Component has not started yet."))

        super().__init__(obj)

    def start(self, args: dict) -> None:
        self.logger.debug("Starting with arguments: %s", args)

        def process_init(start_args: Mapping[str, Any]):
            self.logger.info("Initialising with parameters: %s", start_args)

            return Bootstrap.on_ready(self.initialize)

        self._params = self.init_params(ArgumentReader(args))
        self._params.map(process_init).alt(self.logger.error)

    @property
    def params(self) -> Mapping[str, Any]:
        return self._params.unwrap()

    # noinspection PyMethodMayBeStatic
    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        active = args.read(BaseComponent.ArgKeys.ACTIVE, bool).value_or(True)

        return Success(dict((("active", active),)))

    def initialize(self) -> None:
        super().initialize()

        self.active = self.params["active"]

    @property
    def valid(self) -> bool:
        return self.initialized and is_successful(self._params)

    def activate(self, value: bool = True) -> None:
        # noinspection PyTypeChecker
        self.active = value

    def deactivate(self) -> None:
        self.activate(False)

    @property
    def processing(self) -> bool:
        return super().processing and self.valid and self.active

    def process(self) -> None:
        pass

    def as_game_object(self, obj: Object) -> KX_GameObject:
        # noinspection PyUnresolvedReferences
        return self.object.scene.getGameObjectFromObject(not_empty(obj))

    @property
    def logger_name(self) -> str:
        return ".".join((super().logger_name, self._obj_name))

    def dispose(self) -> None:
        self._params = Result.from_failure(NotStartedError("Component has been disposed already."))

        super().dispose()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.object.name})"


class IDComponent(Generic[T, U], BaseComponent[T], ABC):
    blenderObject: U

    def __init__(self, obj: T) -> None:
        super().__init__(obj)
