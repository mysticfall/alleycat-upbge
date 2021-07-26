from pytest import fixture

from alleycat.ui import Component, Context, MouseMoveEvent, Point
from tests.ui import UI


@fixture
def context() -> Context:
    return UI().create_context()


def test_propagation(context: Context):
    component = Component(context)

    event = MouseMoveEvent(component, Point(10, 10))

    assert not event.propagation_stopped

    event.stop_propagation()

    assert event.propagation_stopped
