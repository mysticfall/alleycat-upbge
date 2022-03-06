import logging
from abc import ABC
from dataclasses import dataclass
from logging import Logger
from types import ModuleType
from typing import Dict, Tuple

from alleycat.test import mock_module


# noinspection PyPep8Naming
@dataclass
class SCA_InputEvent:
    status: int
    queue: Tuple[int] = ()
    values: Tuple[int] = ()


# noinspection PyPep8Naming
class SCA_PythonMouse:
    events: Dict[int, SCA_InputEvent] = dict()

    activeInputs: Dict[int, SCA_InputEvent] = dict()

    position: Tuple[float, float] = (0.5, 0.5)

    visible: bool = True


def setup() -> None:
    def setup_bge(module: ModuleType):
        module.types = mock_module("bge.types", setup_types)
        module.logic = mock_module("bge.logic", setup_logic)
        module.events = mock_module("bge.events", setup_events)

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
    module.SCA_PythonMouse = SCA_PythonMouse


# noinspection PyPep8Naming
def setup_logic(module: ModuleType) -> None:
    module._clock_time = 0

    def get_frame_time():
        return 0

    def get_clock_time():
        # noinspection PyProtectedMember
        return module._clock_time

    def set_clock_time(time):
        module._clock_time = time

    def get_real_time():
        return 0

    module.getFrameTime = get_frame_time
    module.getClockTime = get_clock_time
    module.setClockTime = set_clock_time
    module.getRealTime = get_real_time

    module.KX_INPUT_NONE = 0
    module.KX_INPUT_JUST_ACTIVATED = 1
    module.KX_INPUT_ACTIVE = 2
    module.KX_INPUT_JUST_RELEASED = 3

    module.mouse = SCA_PythonMouse()


# noinspection PyPep8Naming,SpellCheckingInspection
def setup_events(module: ModuleType) -> None:
    module.LEFTMOUSE = 116
    module.MIDDLEMOUSE = 117
    module.RIGHTMOUSE = 118
