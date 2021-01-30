import logging
from abc import ABC, abstractmethod
from typing import Callable, Generic, Optional, Sequence, TypeVar

from alleycat.reactive import RP, RV, ReactiveObject, functions as rv
from rx import Observable, operators as ops

from alleycat.log import LoggingSupport

T = TypeVar("T")


class Input(LoggingSupport, ReactiveObject, Generic[T], ABC):
    value: RV[T] = rv.new_view()

    enabled: RP[bool] = rv.new_property()

    def __init__(self, init_value: Optional[T] = None, repeat: bool = True, enabled: bool = True) -> None:
        super().__init__()

        operators = [ops.filter(lambda _: self.enabled)]

        modifiers = self.modifiers

        assert modifiers is not None, "Operators cannot be None."

        for mod in modifiers:
            operators.append(mod)

        if init_value is not None:
            operators.append(ops.start_with(init_value))

        if not repeat:
            operators.append(ops.distinct_until_changed())

        operators.append(ops.do_action(self.log_value))

        self._repeat = bool(repeat)

        # noinspection PyTypeChecker
        self.enabled = bool(enabled)
        self.value = self.create().pipe(*operators)

        self.logger.debug("Input created: init_value=%s, enabled=%s, repeat=%s.", init_value, enabled, repeat)

    @property
    def modifiers(self) -> Sequence[Callable[[Observable], Observable]]:
        return ()

    @property
    def repeat(self) -> bool:
        return self._repeat

    @abstractmethod
    def create(self) -> Observable:
        pass

    def log_value(self, value: T) -> None:
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("Input value: %s.", value)

    def dispose(self) -> None:
        self.logger.debug("Disposing input.")

        super().dispose()
