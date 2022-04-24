from abc import ABC
from functools import partial
from typing import Any, OrderedDict

from bge.types import KX_GameObject, KX_PythonComponent

from alleycat.common import LoggingSupport
from alleycat.core import Bootstrap, PropertyHolder


class BaseProxy(PropertyHolder, LoggingSupport, ABC):

    def start(self, args: OrderedDict[str, Any]) -> None:
        Bootstrap.when_ready(partial(super().start, args))


class BaseComponent(BaseProxy, KX_PythonComponent, ABC):
    pass


class BaseObject(BaseProxy, KX_GameObject, ABC):
    pass
