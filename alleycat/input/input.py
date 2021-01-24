from abc import ABC, abstractmethod
from typing import Callable, Generic, Optional, Sequence, TypeVar

from alleycat.reactive import RP, RV, ReactiveObject, functions as rv
from rx import Observable, operators as ops

T = TypeVar("T")


class Input(ReactiveObject, Generic[T], ABC):
    value: RV[T] = rv.new_view()

    enabled: RP[bool] = rv.new_property()

    def __init__(self, init_value: Optional[T] = None, enabled: bool = True) -> None:
        super().__init__()

        operators = [ops.filter(lambda _: self.enabled)]

        modifiers = self.modifiers

        assert modifiers is not None, "Operators cannot be None."

        for mod in modifiers:
            operators.append(mod)

        if init_value is not None:
            operators.append(ops.start_with(init_value))

        operators.append(ops.distinct_until_changed())

        # noinspection PyTypeChecker
        self.enabled = bool(enabled)
        self.value = self.create().pipe(*operators)

    @property
    def modifiers(self) -> Sequence[Callable[[Observable], Observable]]:
        return ()

    @abstractmethod
    def create(self) -> Observable:
        pass
