# noinspection PyPep8Naming
from types import ModuleType

from tests.mock import mock_module


def setup() -> None:
    mock_module("bge.types", setup_types)


# noinspection PyPep8Naming
def setup_types(module: ModuleType) -> None:
    class SCA_IObject:
        pass

    # noinspection PyUnusedLocal
    class KX_GameObject:
        def __init__(self, parent: SCA_IObject) -> None:
            pass

    class KX_PythonComponent:
        pass

    module.SCA_IObject = SCA_IObject
    module.KX_GameObject = KX_GameObject
    module.KX_PythonComponent = KX_PythonComponent
