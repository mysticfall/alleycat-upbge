from abc import ABC
from itertools import chain
from typing import Mapping

from alleycat.reactive import RP, functions as rv
from bge.types import KX_GameObject
from mathutils import Vector
from returns.iterables import Fold
from returns.result import ResultE, Success

from alleycat.common import ArgumentReader
from alleycat.game import BaseComponent, require_component


class Vision(BaseComponent[KX_GameObject], ABC):
    looking_at: RP[Vector] = rv.from_value(Vector((0, -1, 0)))

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)


class Sighted(BaseComponent[KX_GameObject], ABC):

    @property
    def vision(self) -> Vision:
        return self.params["vision"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        result = Fold.collect((
            require_component(self.object, Vision).map(lambda v: ("vision", v)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))


class Eyes(Vision):

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)
