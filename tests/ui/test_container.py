from alleycat.reactive import functions as rv
from pytest import fixture
from returns.maybe import Nothing, Some

from alleycat.ui import Bounds, Component, Container, Context, Dimension, Frame, Panel, Point
from alleycat.ui.layout import AbsoluteLayout
from tests.ui import UI


@fixture
def context() -> Context:
    return UI().create_context()


def test_children(context: Context):
    container = Container(context)

    children = []

    rv.observe(container, "children").subscribe(children.append)

    child1 = Panel(context)
    child2 = Panel(context)

    assert children == [()]

    container.add(child1)

    assert container.children == (child1,)
    assert children == [(), (child1,)]

    container.add(child2)

    assert container.children == (child1, child2)
    assert children == [(), (child1,), (child1, child2)]

    container.remove(child1)

    assert container.children == (child2,)


def test_component_at_with_hierarchy(context: Context):
    parent = Container(context)
    parent.bounds = Bounds(0, 0, 200, 200)

    child = Container(context)
    child.bounds = Bounds(50, 50, 100, 100)

    grand_child = Container(context)
    grand_child.bounds = Bounds(25, 25, 50, 50)

    child.add(grand_child)
    parent.add(child)

    assert parent.component_at(Point(-1, 0)) == Nothing
    assert parent.component_at(Point(201, 0)) == Nothing
    assert parent.component_at(Point(200, 201)) == Nothing
    assert parent.component_at(Point(-1, 200)) == Nothing

    assert parent.component_at(Point(50, 49)) == Some(parent)
    assert parent.component_at(Point(151, 50)) == Some(parent)
    assert parent.component_at(Point(150, 151)) == Some(parent)
    assert parent.component_at(Point(49, 150)) == Some(parent)

    assert parent.component_at(Point(50, 50)) == Some(child)
    assert parent.component_at(Point(150, 50)) == Some(child)
    assert parent.component_at(Point(150, 150)) == Some(child)
    assert parent.component_at(Point(50, 150)) == Some(child)

    assert parent.component_at(Point(75, 75)) == Some(grand_child)
    assert parent.component_at(Point(125, 75)) == Some(grand_child)
    assert parent.component_at(Point(125, 125)) == Some(grand_child)
    assert parent.component_at(Point(75, 125)) == Some(grand_child)

    assert parent.component_at(Point(74, 75)) == Some(child)
    assert parent.component_at(Point(125, 74)) == Some(child)
    assert parent.component_at(Point(126, 125)) == Some(child)
    assert parent.component_at(Point(75, 126)) == Some(child)


def test_component_at_with_layers(context: Context):
    parent = Container(context)
    parent.bounds = Bounds(0, 0, 200, 200)

    bottom = Container(context)
    bottom.bounds = Bounds(0, 0, 100, 100)

    middle = Container(context)
    middle.bounds = Bounds(100, 100, 100, 100)

    top = Container(context)
    top.bounds = Bounds(50, 50, 100, 100)

    parent.add(bottom)
    parent.add(middle)
    parent.add(top)

    assert parent.component_at(Point(200, 0)) == Some(parent)
    assert parent.component_at(Point(0, 200)) == Some(parent)

    assert parent.component_at(Point(0, 0)) == Some(bottom)
    assert parent.component_at(Point(100, 0)) == Some(bottom)
    assert parent.component_at(Point(0, 100)) == Some(bottom)

    assert parent.component_at(Point(200, 100)) == Some(middle)
    assert parent.component_at(Point(200, 200)) == Some(middle)
    assert parent.component_at(Point(100, 200)) == Some(middle)

    assert parent.component_at(Point(100, 100)) == Some(top)
    assert parent.component_at(Point(150, 150)) == Some(top)
    assert parent.component_at(Point(150, 50)) == Some(top)
    assert parent.component_at(Point(50, 150)) == Some(top)


def test_component_parent(context: Context):
    parents = []

    parent1 = Container(context)
    parent2 = Container(context)

    component = Component(context)

    rv.observe(component.parent).subscribe(parents.append)

    assert component.parent == Nothing
    assert parents == [Nothing]

    parent1.add(component)

    assert parent1.children == (component,)

    assert component.parent == Some(parent1)
    assert parents == [Nothing, Some(parent1)]

    parent2.add(component)

    assert component in parent2.children
    assert component not in parent1.children

    assert component.parent == Some(parent2)
    assert parents == [Nothing, Some(parent1), Nothing, Some(parent2)]

    parent2.remove(component)

    assert component.parent == Nothing
    assert parents == [Nothing, Some(parent1), Nothing, Some(parent2), Nothing]


def test_absolute_layout(context: Context):
    container = Frame(context, AbsoluteLayout())
    container.bounds = Bounds(30, 30, 200, 200)

    child1 = Panel(context)
    child1.bounds = Bounds(10, 10, 20, 20)

    child2 = Panel(context)
    child2.bounds = Bounds(50, 60, 20, 20)

    container.add(child1)
    container.add(child2)

    context.process()

    assert child1.bounds == Bounds(10, 10, 20, 20)
    assert child2.bounds == Bounds(50, 60, 20, 20)
    assert container.minimum_size == Dimension(0, 0)

    container.bounds = Bounds(20, 20, 100, 100)
    child1.minimum_size_override = Some(Dimension(400, 400))
    child2.bounds = Bounds(-30, -40, 50, 50)

    context.process()

    assert child1.bounds == Bounds(10, 10, 400, 400)
    assert child2.bounds == Bounds(-30, -40, 50, 50)
    assert container.minimum_size == Dimension(0, 0)


def test_validation(context: Context):
    container = Frame(context)
    container.bounds = Bounds(30, 30, 200, 200)

    child = Panel(context)
    child.bounds = Bounds(10, 10, 20, 20)

    container.validate()
    assert container.valid

    container.add(child)

    assert not container.valid

    container.validate()
    child.bounds = Bounds(10, 10, 30, 30)

    assert not container.valid

    container.validate()
    child.preferred_size_override = Some(Dimension(60, 60))

    assert not container.valid

    container.validate()
    child.minimum_size_override = Some(Dimension(10, 10))

    assert not container.valid

    container.validate()
    child.visible = False

    assert not container.valid

    container.validate()
    container.remove(child)

    assert not container.valid
