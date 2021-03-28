from abc import ABC
from collections import OrderedDict
from functools import cached_property
from typing import Final, Generic, TypeVar

from alleycat.reactive import RP, ReactiveObject, functions as rv
from bge.types import KX_GameObject
from rx import Observable, operators as ops

from alleycat.common import ArgumentReader, BaseComponent


class Activatable(ReactiveObject, ABC):
    active: RP[bool] = rv.from_value(True)

    def __init__(self) -> None:
        super().__init__()

    def activate(self, value: bool = True) -> None:
        # noinspection PyTypeChecker
        self.active = value

    def deactivate(self) -> None:
        self.activate(False)


T = TypeVar("T", bound=KX_GameObject)


class ActivatableComponent(Generic[T], BaseComponent[T], Activatable, ABC):
    class ArgKeys:
        ACTIVE: Final = "Active"

    args = OrderedDict((
        (ArgKeys.ACTIVE, True),
    ))

    def __init__(self, obj: T) -> None:
        super().__init__(obj)

    def start(self, args: dict) -> None:
        super().start(args)

        props = ArgumentReader(args)

        self.active = props.read(self.ArgKeys.ACTIVE, bool).value_or(True)

        self.logger.debug("args['%s'] = %s", self.ArgKeys.ACTIVE, self.active)

    @cached_property
    def on_update(self) -> Observable:
        return super().on_update.pipe(ops.filter(lambda _: self.active))
