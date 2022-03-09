from abc import ABC, abstractmethod
from collections import OrderedDict
from logging import Logger
from typing import Final, final

from bge.types import KX_GameObject, KX_PythonComponent
from returns.result import Result, ResultE

from alleycat.common import AlreadyDisposedError, NotStartedError
from alleycat.core import ArgumentsHolder

RESULT_NOT_STARTED: Final = Result.from_failure(
    NotStartedError("The proxy has not been started yet."))

RESULT_DISPOSED: Final = Result.from_failure(
    AlreadyDisposedError("The proxy instance has been disposed already."))


class BaseProxy(ArgumentsHolder, ABC):
    _args_values: ResultE[OrderedDict] = RESULT_NOT_STARTED

    @property
    @abstractmethod
    def logger(self) -> Logger:
        pass

    @final
    @property
    def arg_values(self) -> ResultE[OrderedDict]:
        return self._args_values

    @property
    def valid(self) -> bool:
        return isinstance(self.arg_values, Result.success_type)

    def start(self, args: OrderedDict) -> None:
        self._args_values = Result.from_value(args)

        self.logger.info("Created state: %s.", args)

    def dispose(self) -> None:
        self._args_values = RESULT_DISPOSED


class BaseComponent(KX_PythonComponent, BaseProxy, ABC):
    pass


class BaseObject(KX_GameObject, BaseProxy, ABC):
    pass
