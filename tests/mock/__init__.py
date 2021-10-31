import sys
from types import ModuleType
from typing import Callable


def mock_module(name: str, definition: Callable[[ModuleType], None]) -> None:
    if name in sys.modules:
        return

    module = ModuleType(name)

    definition(module)

    sys.modules[name] = module
