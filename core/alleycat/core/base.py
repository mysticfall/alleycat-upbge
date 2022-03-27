from abc import ABC
from collections import OrderedDict
from typing import Final, final

from bge.types import KX_GameObject, KX_PythonComponent
from returns.result import Result, ResultE

from alleycat.common import AlreadyDisposedError, LoggingSupport, NotStartedError
from alleycat.core import ArgumentsHolder

RESULT_NOT_STARTED: Final = Result.from_failure(
    NotStartedError("The proxy has not been started yet."))

RESULT_DISPOSED: Final = Result.from_failure(
    AlreadyDisposedError("The proxy instance has been disposed already."))


class BaseProxy(ArgumentsHolder, LoggingSupport, ABC):
    _start_args: ResultE[OrderedDict] = RESULT_NOT_STARTED

    @final
    @property
    def start_args(self) -> ResultE[OrderedDict]:
        return self._start_args

    @property
    def valid(self) -> bool:
        return isinstance(self.start_args, Result.success_type)

    def start(self, args: OrderedDict) -> None:
        self._start_args = Result.from_value(args)

        self.logger.info("Created state: %s.", args)

    def dispose(self) -> None:
        self._start_args = RESULT_DISPOSED


class BaseComponent(BaseProxy, KX_PythonComponent, ABC):
    pass


class BaseObject(BaseProxy, KX_GameObject, ABC):
    pass
