from pytest import fixture
from returns.maybe import Some

from alleycat.ui import Bounds, Container, Context, Dimension, Frame, Panel
from alleycat.ui.layout import AbsoluteLayout
from tests.ui import UI


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def container(context: Context) -> Container:
    return Frame(context, AbsoluteLayout())


def test_layout(container: Container, context: Context):
    container.bounds = Bounds(30, 30, 200, 200)

    child1 = Panel(context)
    child1.bounds = Bounds(10, 10, 20, 20)

    child2 = Panel(context)
    child2.bounds = Bounds(50, 60, 20, 20)

    container.add(child1)
    container.add(child2)

    assert not container.valid
    context.process()
    assert container.valid

    assert child1.bounds == Bounds(10, 10, 20, 20)
    assert child2.bounds == Bounds(50, 60, 20, 20)

    assert container.minimum_size == Dimension(0, 0)
    assert container.preferred_size == Dimension(0, 0)

    container.bounds = Bounds(20, 20, 100, 100)

    child1.minimum_size_override = Some(Dimension(400, 400))
    child2.bounds = Bounds(-30, -40, 50, 50)

    assert not container.valid
    context.process()
    assert container.valid

    assert child1.bounds == Bounds(10, 10, 400, 400)
    assert child2.bounds == Bounds(-30, -40, 50, 50)
    assert container.minimum_size == Dimension(0, 0)
