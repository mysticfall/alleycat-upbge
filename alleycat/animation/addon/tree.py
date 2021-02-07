from typing import List

from bpy.types import Context, Node, NodeSocketStandard, NodeTree, UILayout
from nodeitems_utils import NodeCategory


class AnimationNodeTree(NodeTree):
    bl_idname: str = "alleycat.animation.addon.AnimationNodeTree"

    bl_label: str = "AlleyCat Animation"

    bl_description: str = "Animation node tree for AlleyCat framework."

    bl_icon: str = "NODETREE"


class AnimationNodeCategory(NodeCategory):

    @classmethod
    def poll(cls, context) -> bool:
        return context.space_data.tree_type == AnimationNodeTree.bl_idname


class NodeSocketAnimation(NodeSocketStandard):
    bl_idname: str = "alleycat.animation.addon.NodeSocketAnimation"

    def draw(self, context: Context, layout: UILayout, node: Node, text: str) -> None:
        layout.label(text=text)

    def draw_color(self, context: Context, node: Node) -> List[float]:
        return [0.388, 0.780, 0.388, 1.0]
