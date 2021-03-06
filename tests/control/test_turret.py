from unittest.mock import patch

from alleycat.reactive import RP, RV, functions as rv
from pytest import approx
from pytest_mock import MockerFixture

from alleycat.common import Lookup
from alleycat.input import InputBinding, InputMap
from tests import MockEuler, MockVector


class TestBinding(InputBinding[MockVector]):
    current: RP[MockVector] = rv.from_value(MockVector((0, 0, 0)))

    value: RV[MockVector] = current.as_view()

    def __init__(self, name: str):
        super().__init__(name)


@patch("mathutils.Vector", MockVector)
@patch("mathutils.Euler", MockEuler)
def test_start(mocker: MockerFixture):
    obj = mocker.patch("bge.types.KX_GameObject")

    binding = TestBinding("rotate")
    input_map = InputMap({"view": Lookup({"rotate": binding})})

    from alleycat.control import TurretControl

    class TestControl(TurretControl):
        pass

    args = dict([
        (TurretControl.ArgKeys.ROTATION_INPUT, "view/rotate"),
        (TurretControl.ArgKeys.ROTATION_SENSITIVITY, 2.0)
    ])

    control = TestControl(obj)
    control.start(args, input_map)

    assert control.pitch == approx(0.0)
    assert control.yaw == approx(0.0)

    binding.current = MockVector((0.3, 0.2))

    assert control.pitch == approx(0.4)
    assert control.yaw == approx(0.6)
