from abc import ABC
from typing import Any, Generic, Mapping, TypeVar

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import ID, Object
from returns.pipeline import is_successful
from returns.result import Result, ResultE
from rx import Observable
from rx.subject import Subject
from validator_collection import not_empty

from alleycat.common import ArgumentReader, IllegalStateError
from alleycat.log import LoggingSupport

T = TypeVar("T", bound=KX_GameObject)
U = TypeVar("U", bound=ID)
V = TypeVar("V")


class NotStartedError(IllegalStateError):
    pass


class BaseComponent(Generic[T], LoggingSupport, ReactiveObject, KX_PythonComponent, ABC):
    object: T

    # noinspection PyUnusedLocal
    def __init__(self, obj: T):
        self._obj_name = obj.name
        self._updater = Subject()
        self._parameters: ResultE[Mapping] = Result.from_failure(NotStartedError("Component has not started yet."))

        super().__init__()

    def start(self, args: dict) -> None:
        self.logger.info("Starting component with arguments: %s", args)

        def invoke_setup(start_args: Mapping[str, Any]):
            self.logger.info("Invoking setup with starting parameters: %s", start_args)

            return self.setup()

        self._parameters = self.validate(ArgumentReader(args))
        self._parameters.map(invoke_setup).alt(self.logger.error)

    @property
    def parameters(self) -> Mapping[str, Any]:
        return self._parameters.unwrap()

    # noinspection PyMethodMayBeStatic
    def validate(self, args: ArgumentReader) -> ResultE[Mapping]:
        return Result.from_value(dict())

    @property
    def valid(self) -> bool:
        return is_successful(self._parameters)

    def setup(self) -> None:
        pass

    @property
    def on_update(self) -> Observable:
        return self._updater

    def update(self) -> None:
        if self.valid:
            self._updater.on_next(None)

    def as_game_object(self, obj: Object) -> KX_GameObject:
        # noinspection PyUnresolvedReferences
        return self.object.scene.getGameObjectFromObject(not_empty(obj))

    @property
    def logger_name(self) -> str:
        return ".".join((super().logger_name, self._obj_name))

    def dispose(self) -> None:
        self._updater.on_completed()
        self._parameters = Result.from_failure(NotStartedError("Component has been disposed already."))

        super().dispose()


class IDComponent(Generic[T, U], BaseComponent[T], ABC):
    blenderObject: U

    def __init__(self, obj: T) -> None:
        super().__init__(obj)
