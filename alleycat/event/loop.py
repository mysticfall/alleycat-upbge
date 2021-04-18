from abc import ABC, abstractmethod

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from rx import Observable
from rx.subject import Subject

from alleycat.log import ErrorHandlerSupport


class EventLoopAware(ErrorHandlerSupport, ReactiveObject, ABC):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @property
    def processing(self) -> bool:
        return True

    @property
    @abstractmethod
    def on_process(self) -> Observable:
        pass

    @abstractmethod
    def process(self) -> None:
        pass


class ComponentLoopSupport(EventLoopAware, KX_PythonComponent, ABC):
    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject) -> None:
        self._on_process = Subject()

        super().__init__()

    @property
    def on_process(self) -> Observable:
        return self._on_process

    def update(self) -> None:
        if self.processing:
            self._on_process.on_next(None)
            self.process()

    def dispose(self) -> None:
        self._on_process.on_completed()
        self._on_process.dispose()

        super().dispose()
