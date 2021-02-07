from typing import List

from bpy.props import FloatProperty
from bpy.types import Context, Node, NodeSocketStandard, UILayout


class NodeSocketFloat0To1(NodeSocketStandard):
    bl_idname: str = "alleycat.common.NodeSocketFloat0To1"

    default_value: FloatProperty(name="Value", default=1.0, min=0.0, max=1.0)  # type:ignore

    def draw(self, context: Context, layout: UILayout, node: Node, text: str) -> None:
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context: Context, node: Node) -> List[float]:
        return [0.631, 0.631, 0.631, 1.0]
