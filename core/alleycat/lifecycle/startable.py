from abc import ABC
from typing import Any, Final, OrderedDict, final

from reactivex import Observable, Subject
from returns.result import Result, ResultE
from validator_collection import dict as dict_type

from alleycat.common import IllegalStateError, MapReader
from alleycat.lifecycle import BaseDisposable, RESULT_DISPOSED


class NotStartedError(IllegalStateError):
    pass


class AlreadyStartedError(IllegalStateError):
    pass


RESULT_NOT_STARTED: Final = Result.from_failure(
    NotStartedError("The object has not been started yet."))


class Startable(BaseDisposable, ABC):
    def __init__(self) -> None:
        super().__init__()

        self.__started = False
        self.__start_args: ResultE[MapReader] = RESULT_NOT_STARTED
        self.__on_start = Subject[None]()

    @final
    @property
    def started(self) -> bool:
        return self.__started

    @final
    @property
    def on_start(self) -> Observable[None]:
        return self.__on_start

    @final
    @property
    def start_args(self) -> ResultE[MapReader]:
        return self.__start_args

    def start(self, args: OrderedDict[str, Any]) -> None:
        if self.__started:
            raise AlreadyStartedError("The object has already started.")

        self.__start_args = Result.from_value(MapReader(dict_type(args, allow_empty=True)))

        self._do_start()

        self.__started = True
        self.__on_start.on_next(None)

    def _do_start(self) -> None:
        pass

    @final
    def _check_started(self) -> None:
        if not self.started:
            raise RESULT_NOT_STARTED.failure()

    def dispose(self) -> None:
        super().dispose()

        self.__on_start.on_completed()
        self.__on_start.dispose()

        self.__start_args = RESULT_DISPOSED
