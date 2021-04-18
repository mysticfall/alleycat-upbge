from collections import OrderedDict
from itertools import chain

from bge.types import KX_GameObject

from alleycat.actor import Mobile, Sighted
from alleycat.animation.runtime import Animating
from alleycat.game import Entity


class Character(Sighted, Mobile, Animating, Entity):
    args = OrderedDict(chain(Entity.args.items(), Animating.args.items()))

    def __init__(self, obj: KX_GameObject):
        super().__init__(obj)

    def process(self) -> None:
        pass
