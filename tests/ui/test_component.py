from typing import Iterable

from alleycat.reactive import functions as rv
from cairocffi import Context as Graphics
from pytest import fixture
from returns.maybe import Nothing, Some

from alleycat.ui import Bounds, Component, ComponentUI, Container, Context, Dimension, MouseMoveEvent, Panel, Point, \
    RGBA
from tests.ui import UI


@fixture
def context() -> Context:
    return UI().create_context()


def test_offset(context: Context):
    parent = Panel(context)
    parent.bounds = Bounds(10, 20, 80, 60)

    grand_parent = Container(context)
    grand_parent.bounds = Bounds(20, 10, 40, 20)

    component = Component(context)
    component.bounds = Bounds(5, 5, 10, 10)

    assert component.offset == Point(0, 0)

    component.bounds = Bounds(10, 20, 10, 10)

    assert component.offset == Point(0, 0)

    parent.add(component)

    assert component.offset == Point(10, 20)

    parent.bounds = parent.bounds.copy(x=30, y=-10)

    assert component.offset == Point(30, -10)

    grand_parent.add(parent)

    assert component.offset == Point(50, 0)

    grand_parent.bounds = grand_parent.bounds.copy(x=-10, y=50)

    assert component.offset == Point(20, 40)


def test_position_of(context: Context):
    parent = Container(context)
    parent.bounds = Bounds(10, 20, 80, 60)

    component = Component(context)
    component.bounds = Bounds(5, 5, 10, 10)

    parent.add(component)

    event = MouseMoveEvent(component, Point(30, 40))

    assert component.position_of(event) == Point(20, 20)


def test_resolve_color(context: Context):
    class Fixture(Component):
        @property
        def style_fallback_prefixes(self) -> Iterable[str]:
            yield "Type"
            yield "Parent"
            yield "GrandParent"

    component = Fixture(context)

    prefixes = list(component.style_fallback_prefixes)
    keys = list(component.style_fallback_keys("color"))

    laf = context.look_and_feel

    assert prefixes == ["Type", "Parent", "GrandParent"]
    assert keys == ["Type.color", "Parent.color", "GrandParent.color", "color"]

    assert component.resolve_color("color") == Nothing

    laf.set_color("GrandParent.color", RGBA(1, 0, 0, 1))
    assert component.resolve_color("color").unwrap() == RGBA(1, 0, 0, 1)

    laf.set_color("GreatGrandParent.color", RGBA(0, 0, 0, 1))
    assert component.resolve_color("color").unwrap() == RGBA(1, 0, 0, 1)

    component.set_color("color", RGBA(0, 1, 0, 1))
    assert component.resolve_color("color").unwrap() == RGBA(0, 1, 0, 1)

    laf.set_color("color", RGBA(1, 1, 1, 1))
    assert component.resolve_color("color").unwrap() == RGBA(0, 1, 0, 1)


def test_validation(context: Context):
    minimum_size = Dimension(10, 10)
    preferred_size = Dimension(20, 20)

    class FixtureComponent(Component):
        def create_ui(self) -> ComponentUI:
            return FixtureUI()

    class FixtureUI(ComponentUI):
        def minimum_size(self, component: Component) -> Dimension:
            return minimum_size

        def preferred_size(self, component: Component) -> Dimension:
            return preferred_size

        def draw(self, g: Graphics, component: Component) -> None:
            pass

    comp = FixtureComponent(context)

    comp.validate()
    assert comp.valid

    comp.invalidate()
    assert not comp.valid

    comp.validate()
    assert comp.valid

    minimum_size = Dimension(30, 30)
    preferred_size = Dimension(40, 40)

    assert comp.minimum_size == Dimension(10, 10)
    assert comp.preferred_size == Dimension(20, 20)

    comp.validate()

    assert comp.minimum_size == Dimension(10, 10)
    assert comp.preferred_size == Dimension(20, 20)

    comp.validate(force=True)

    assert comp.minimum_size == Dimension(30, 30)
    assert comp.preferred_size == Dimension(40, 40)


# noinspection DuplicatedCode
def test_minimum_size(context: Context):
    minimum_size = Dimension(10, 10)

    class FixtureComponent(Component):
        def create_ui(self) -> ComponentUI:
            return FixtureUI()

    class FixtureUI(ComponentUI):
        def minimum_size(self, component: Component) -> Dimension:
            return minimum_size

        def draw(self, g: Graphics, component: Component) -> None:
            pass

    comp = FixtureComponent(context)

    sizes = []
    effective_sizes = []

    rv.observe(comp.minimum_size_override).subscribe(sizes.append)
    rv.observe(comp.minimum_size).subscribe(effective_sizes.append)

    assert comp.minimum_size_override == Nothing
    assert comp.minimum_size == Dimension(10, 10)
    assert sizes == [Nothing]
    assert effective_sizes == [Dimension(10, 10)]

    comp.bounds = Bounds(10, 20, 100, 50)
    comp.validate(force=True)

    assert comp.bounds == Bounds(10, 20, 100, 50)

    comp.minimum_size_override = Some(Dimension(200, 100))
    comp.validate(force=True)

    assert comp.minimum_size_override == Some(Dimension(200, 100))
    assert comp.minimum_size == Dimension(200, 100)
    assert sizes[1:] == [Some(Dimension(200, 100))]
    assert effective_sizes[1:] == [Dimension(200, 100)]
    assert comp.bounds == Bounds(10, 20, 200, 100)

    minimum_size = Dimension(240, 260)
    comp.validate(force=True)

    assert comp.minimum_size_override == Some(Dimension(200, 100))
    assert comp.minimum_size == Dimension(200, 100)
    assert len(effective_sizes) == 2
    assert sizes[1:] == [Some(Dimension(200, 100))]
    assert effective_sizes[1:] == [Dimension(200, 100)]
    assert comp.bounds == Bounds(10, 20, 200, 100)

    comp.bounds = Bounds(0, 0, 30, 40)
    comp.validate(force=True)

    assert comp.bounds == Bounds(0, 0, 200, 100)

    comp.minimum_size_override = Nothing
    comp.validate(force=True)

    assert comp.minimum_size_override == Nothing
    assert comp.minimum_size == Dimension(240, 260)
    assert len(effective_sizes) == 3
    assert sizes[2:] == [Nothing]
    assert effective_sizes[2:] == [Dimension(240, 260)]
    assert comp.bounds == Bounds(0, 0, 240, 260)


# noinspection DuplicatedCode
def test_preferred_size(context: Context):
    preferred_size = Dimension(10, 10)

    class FixtureComponent(Component):
        pass

    class FixtureUI(ComponentUI):
        def preferred_size(self, component: Component) -> Dimension:
            return preferred_size

        def draw(self, g: Graphics, component: Component) -> None:
            pass

    context.look_and_feel.register_ui(FixtureComponent, FixtureUI)

    comp = FixtureComponent(context)

    sizes = []
    effective_sizes = []

    rv.observe(comp.preferred_size_override).subscribe(sizes.append)
    rv.observe(comp.preferred_size).subscribe(effective_sizes.append)

    assert comp.preferred_size_override == Nothing
    assert comp.preferred_size == Dimension(10, 10)
    assert sizes == [Nothing]
    assert effective_sizes == [Dimension(10, 10)]

    comp.preferred_size_override = Some(Dimension(100, 80))
    comp.validate(force=True)

    assert comp.preferred_size_override == Some(Dimension(100, 80))
    assert comp.preferred_size == Dimension(100, 80)
    assert sizes[1:] == [Some(Dimension(100, 80))]
    assert effective_sizes[1:] == [Dimension(100, 80)]

    preferred_size = Dimension(240, 300)
    comp.validate(force=True)

    assert comp.preferred_size_override == Some(Dimension(100, 80))
    assert comp.preferred_size == Dimension(100, 80)
    assert sizes[1:] == [Some(Dimension(100, 80))]
    assert effective_sizes[1:] == [Dimension(100, 80)]

    comp.preferred_size_override = Nothing
    comp.validate(force=True)

    assert comp.preferred_size_override == Nothing
    assert comp.preferred_size == Dimension(240, 300)
    assert sizes[2:] == [Nothing]
    assert effective_sizes[2:] == [Dimension(240, 300)]

    comp.minimum_size_override = Some(Dimension(400, 360))
    comp.validate(force=True)

    assert comp.preferred_size == Dimension(400, 360)
    assert effective_sizes[3:] == [Dimension(400, 360)]

    comp.preferred_size_override = Some(Dimension(300, 300))
    comp.validate(force=True)

    assert comp.preferred_size == Dimension(400, 360)
    assert sizes[3:] == [Some(Dimension(400, 360))]
    assert effective_sizes[3:] == [Dimension(400, 360)]
