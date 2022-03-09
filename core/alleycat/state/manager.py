from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Generic, TypeVar, final

from returns.result import Result, ResultE
from rx import Observable, operators as ops
from rx.subject import ReplaySubject

from alleycat.core import BaseProxy, RESULT_DISPOSED, RESULT_NOT_STARTED

TState = TypeVar("TState")


class StateManager(BaseProxy, Generic[TState], ABC):

    def __init__(self):
        super().__init__()

        self._state = RESULT_NOT_STARTED
        self._state_subject = ReplaySubject[TState](buffer_size=1)

    @property
    @abstractmethod
    def init_state(self) -> ResultE[TState]:
        pass

    @abstractmethod
    def next_state(self, state: TState) -> ResultE[TState]:
        pass

    @final
    @property
    def state(self) -> ResultE[TState]:
        return self._state

    @property
    def on_state_change(self) -> Observable[TState]:
        return self._state_subject.pipe(ops.distinct_until_changed())

    def update(self) -> None:
        if not self.valid:
            return

        self._state = self.state.bind(self.next_state)

        if isinstance(self._state, Result.success_type):
            self._state_subject.on_next(self._state.unwrap())
        else:
            self.logger.warning("Failed to update state: %s", self._state.failure())

    def start(self, args: OrderedDict) -> None:
        super().start(args)

        self._state = self.init_state

    def dispose(self) -> None:
        self._state_subject.on_completed()
        self._state_subject.dispose()

        self._state = RESULT_DISPOSED

        super().dispose()
