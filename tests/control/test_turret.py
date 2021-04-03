from unittest.mock import patch

from alleycat.reactive import RP, RV, functions as rv
from bge.types import KX_GameObject
from pytest import approx
from pytest_mock import MockerFixture

from alleycat.common import ActivatableComponent
from alleycat.input import InputBinding
from tests import MockEuler, MockVector


class TestBinding(InputBinding[MockVector]):
    current: RP[MockVector] = rv.from_value(MockVector((0, 0, 0)))

    value: RV[MockVector] = current.as_view()

    def __init__(self, name: str):
        super().__init__(name)


@patch("mathutils.Vector", MockVector)
@patch("mathutils.Euler", MockEuler)
def test_start(mocker: MockerFixture):
    binding = TestBinding("rotate")

    from alleycat.control import TurretControl

    class TestControl(TurretControl[KX_GameObject]):
        def __init__(self, obj: KX_GameObject):
            obj.name = "test"

            super().__init__(obj)

    args = dict([
        (ActivatableComponent.ArgKeys.ACTIVE, True),
    ])

    control = TestControl(mocker.patch("bge.types.KX_GameObject"))
    control.start(args)

    assert control.pitch == approx(0.0)
    assert control.yaw == approx(0.0)
