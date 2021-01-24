import logging
from abc import ABC
from logging import Logger
from types import ModuleType

from alleycat.test import mock_module


def setup() -> None:
    def setup_bge(module: ModuleType):
        module.types = mock_module("bge.types", setup_types)
        module.logic = mock_module("bge.logic", setup_logic)

    mock_module("bge", setup_bge)


# noinspection PyPep8Naming
def setup_types(module: ModuleType) -> None:
    class SCA_IObject:
        pass

    class KX_PythonProxy(ABC):

        @property
        def logger(self) -> Logger:
            return logging.getLogger()

    class KX_GameObject(KX_PythonProxy):
        def __init__(self, *arg):
            pass

    class KX_PythonComponent(KX_PythonProxy):
        pass

    module.SCA_IObject = SCA_IObject
    module.KX_GameObject = KX_GameObject
    module.KX_PythonComponent = KX_PythonComponent


def setup_logic(module: ModuleType) -> None:
    module._frame_time = 0

    def get_frame_time():
        # noinspection PyProtectedMember
        return module._frame_time

    def set_frame_time(time):
        module._frame_time = time

    module.getFrameTime = get_frame_time
    module.setFrameTime = set_frame_time
