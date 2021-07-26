from typing import Sequence

from pytest import fixture

from alleycat.ui import Context, Dimension, FakeMouseInput, Input, MouseInput
from tests.ui import FixtureContext, FixtureToolkit


@fixture
def toolkit() -> FixtureToolkit:
    class TestMouseInput(FakeMouseInput):
        pass

    class ToolkitFixture(FixtureToolkit):

        def create_inputs(self, ctx: Context) -> Sequence[Input]:
            return TestMouseInput(ctx),

    return ToolkitFixture()


@fixture
def context(toolkit: FixtureToolkit) -> Context:
    return FixtureContext(Dimension(10, 10), toolkit)


def test_inputs(context: Context):
    mouse_input = MouseInput.input(context)

    assert mouse_input
    assert type(mouse_input).__name__ == "TestMouseInput"
