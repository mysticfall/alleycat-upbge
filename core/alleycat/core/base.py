from abc import ABC
from collections import OrderedDict
from functools import partial

from bge.types import KX_GameObject, KX_PythonComponent

from alleycat.common import LoggingSupport
from alleycat.core import ArgumentsHolder, Bootstrap


class BaseProxy(ArgumentsHolder, LoggingSupport, ABC):

    def start(self, args: OrderedDict) -> None:
        Bootstrap.when_ready(partial(super().start, args))


class BaseComponent(BaseProxy, KX_PythonComponent, ABC):
    pass


class BaseObject(BaseProxy, KX_GameObject, ABC):
    pass
