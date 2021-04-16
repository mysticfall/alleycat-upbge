from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping

from bge.types import KX_GameObject
from dependency_injector.wiring import inject
from returns.iterables import Fold
from returns.result import ResultE, Success

from alleycat.common import ActivatableComponent, ArgumentReader


class Entity(ActivatableComponent[KX_GameObject], ABC):
    class ArgKeys(ActivatableComponent.ArgKeys):
        NAME: Final = "Name"

    args = OrderedDict(chain(ActivatableComponent.args.items(), (
        (ArgKeys.NAME, "Entity"),
    )))

    def __init__(self, obj: KX_GameObject):
        super().__init__(obj)

    @property
    def name(self) -> str:
        return self.params["name"]

    @inject
    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        name = args \
            .require(self.ArgKeys.NAME, str) \
            .alt(lambda _: ValueError("Missing entity's name."))

        result = Fold.collect((
            name.map(lambda n: ("name", n)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))
