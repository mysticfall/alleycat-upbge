from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Generic, TypeVar, final

from reactivex import Observable, operators as ops
from reactivex.subject import ReplaySubject
from returns.pipeline import is_successful
from returns.result import ResultE

from alleycat.common import LoggingSupport
from alleycat.lifecycle import RESULT_DISPOSED, RESULT_NOT_STARTED, Startable, Updatable

TState = TypeVar("TState")


class StateManager(Startable, Updatable, LoggingSupport, Generic[TState], ABC):

    def __init__(self) -> None:
        super().__init__()

        self.__state = RESULT_NOT_STARTED
        self.__state_subject = ReplaySubject[TState](buffer_size=1)

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
        return self.__state

    @property
    def on_state_change(self) -> Observable[TState]:
        return self.__state_subject.pipe(ops.distinct_until_changed())

    def _do_update(self) -> None:
        self.__state = self.state.bind(self.next_state)

        if is_successful(self.__state):
            self.__state_subject.on_next(self.__state.unwrap())
        else:
            self.logger.warning("Failed to update state: %s", self.__state.failure())

    def start(self, args: OrderedDict) -> None:
        super().start(args)

        self.__state = self.init_state

    def dispose(self) -> None:
        self.__state_subject.on_completed()
        self.__state_subject.dispose()

        self.__state = RESULT_DISPOSED

        super().dispose()
