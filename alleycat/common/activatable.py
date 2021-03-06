from abc import ABC
from collections import OrderedDict
from typing import Final

from alleycat.reactive import RP, functions as rv

from alleycat.common import ArgumentReader, BaseComponent


class Activatable(ABC):
    active: RP[bool] = rv.from_value(True)


class ActivatableComponent(BaseComponent, Activatable, ABC):
    class ArgKeys:
        ACTIVE: Final = "Active"

    args = OrderedDict((
        (ArgKeys.ACTIVE, True),
    ))

    def start(self, args: dict) -> None:
        props = ArgumentReader(args)

        self.active = props.read(self.ArgKeys.ACTIVE, bool).value_or(True)

        self.logger.debug("args['%s'] = %s", self.ArgKeys.ACTIVE, self.active)

    def update(self) -> None:
        if self.valid and self.active:
            for callback in self.callbacks:
                callback()
