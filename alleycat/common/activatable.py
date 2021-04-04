from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import Final, Generic, Mapping, TypeVar

from alleycat.reactive import RP, ReactiveObject, functions as rv
from bge.types import KX_GameObject
from returns.iterables import Fold
from returns.result import ResultE, Success

from alleycat.common import ArgumentReader, BaseComponent


class Activatable(ReactiveObject, ABC):
    active: RP[bool] = rv.from_value(True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def activate(self, value: bool = True) -> None:
        # noinspection PyTypeChecker
        self.active = value

    def deactivate(self) -> None:
        self.activate(False)


T = TypeVar("T", bound=KX_GameObject)


class ActivatableComponent(Generic[T], Activatable, BaseComponent[T], ABC):
    class ArgKeys:
        ACTIVE: Final = "Active"

    args = OrderedDict((
        (ArgKeys.ACTIVE, True),
    ))

    def __init__(self, obj: T) -> None:
        super().__init__(obj=obj)

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        # noinspection PyTypeChecker
        active = args.require(self.ArgKeys.ACTIVE, bool).lash(lambda _: Success(False))

        result = Fold.collect((
            active.map(lambda a: ("active", a)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        self.active = self.params["active"]

    @property
    def processing(self) -> bool:
        # noinspection PyUnresolvedReferences
        return super().processing and self.active
