from types import ModuleType
from typing import Callable

import sys

from .asserts import assert_failure, assert_success


def mock_module(name: str, definition: Callable[[ModuleType], None]) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]

    module = ModuleType(name)

    definition(module)

    sys.modules[name] = module

    return module
