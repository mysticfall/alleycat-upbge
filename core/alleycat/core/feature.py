from abc import ABC, abstractmethod
from collections import OrderedDict

from bge.types import KX_PythonComponent
from dependency_injector.providers import Configuration


class Feature(KX_PythonComponent, ABC):

    def start(self, args: OrderedDict) -> None:
        pass

    @abstractmethod
    def config(self, config: Configuration):
        pass
