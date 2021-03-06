from abc import ABC
from collections import OrderedDict
from typing import Final, Generic, TypeVar

from alleycat.reactive import RP, ReactiveObject, functions as rv
from bge.types import KX_GameObject

from alleycat.common import ArgumentReader, BaseComponent


class Activatable(ReactiveObject, ABC):
    active: RP[bool] = rv.from_value(True)

    def __init__(self, **kwargs) -> None:
        super().__init__()


T = TypeVar("T", bound=KX_GameObject)


class ActivatableComponent(Generic[T], BaseComponent[T], Activatable, ABC):
    class ArgKeys:
        ACTIVE: Final = "Active"

    args = OrderedDict((
        (ArgKeys.ACTIVE, True),
    ))

    def __init__(self, obj: T) -> None:
        super().__init__(obj=obj)

    def start(self, args: dict) -> None:
        props = ArgumentReader(args)

        self.active = props.read(self.ArgKeys.ACTIVE, bool).value_or(True)

        self.logger.debug("args['%s'] = %s", self.ArgKeys.ACTIVE, self.active)

    def update(self) -> None:
        if self.valid and self.active:
            for callback in self.callbacks:
                callback()
