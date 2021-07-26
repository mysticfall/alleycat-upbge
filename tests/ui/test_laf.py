from typing import Sequence, Tuple

from cairocffi import Context as Graphics
from pytest import fixture, mark

from alleycat.ui import Button, ComponentUI, Container, Context, Label, LabelButton, LookAndFeel, Panel
from alleycat.ui.component import Component
from alleycat.ui.glass import GlassButtonUI, GlassComponentUI, GlassLabelButtonUI, GlassLabelUI, GlassPanelUI
from tests.ui import UI


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def glass_laf(context: Context) -> LookAndFeel:
    class LookAndFeelFixture(LookAndFeel):
        @property
        def default_ui(self) -> ComponentUI[Component]:
            return GlassComponentUI()

    return LookAndFeelFixture(context.toolkit)


def test_register_ui(context: Context):
    class CustomPanelUI(ComponentUI[Panel]):
        def draw(self, g: Graphics, component: Panel) -> None:
            pass

    laf = context.look_and_feel
    laf.register_ui(Panel, CustomPanelUI)

    panel_ui = laf.create_ui(Panel(context))
    container_ui = laf.create_ui(Container(context))

    assert isinstance(panel_ui, CustomPanelUI)
    assert not isinstance(container_ui, CustomPanelUI)


@mark.parametrize("types", (
        ((LabelButton, GlassLabelButtonUI), (Button, GlassButtonUI), (Label, GlassLabelUI)),
        ((Button, GlassButtonUI), (Label, GlassLabelUI), (LabelButton, GlassLabelButtonUI))))
def test_register_ui_order(glass_laf: LookAndFeel, context: Context, types: Sequence[Tuple[Component, ComponentUI]]):
    for (comp, ui) in types:
        glass_laf.register_ui(comp, ui)

    for (comp, ui) in types:
        assert isinstance(glass_laf.create_ui(comp(context)), ui)


def test_deregister_ui(context: Context):
    laf = context.look_and_feel

    def create_panel_ui():
        return laf.create_ui(Panel(context))

    def create_component_ui():
        return laf.create_ui(Component(context))

    assert isinstance(create_panel_ui(), GlassPanelUI)
    assert isinstance(create_component_ui(), GlassComponentUI)

    laf.deregister_ui(Panel)

    assert not isinstance(create_panel_ui(), GlassPanelUI)
    assert isinstance(create_component_ui(), GlassComponentUI)
