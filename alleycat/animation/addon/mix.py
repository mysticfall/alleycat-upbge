from bpy.types import Context, NodeLink

from alleycat.animation import AnimationContext
from alleycat.animation.addon import AnimationNode, NodeSocketAnimation
from alleycat.common import NodeSocketFloat0To1


class MixAnimationNode(AnimationNode):
    bl_idname: str = "alleycat.animation.addon.MixAnimationNode"

    bl_label: str = "Mix"

    bl_icon: str = "ACTION"

    def init(self, context: Context) -> None:
        self.inputs.new(NodeSocketFloat0To1.bl_idname, "Mix")

        self.inputs.new(NodeSocketAnimation.bl_idname, "Input")
        self.inputs.new(NodeSocketAnimation.bl_idname, "Input")

        self.outputs.new(NodeSocketAnimation.bl_idname, "Output")

    def advance(self, context: AnimationContext) -> None:
        link: NodeLink = self.inputs[1].links[0]

        # print(self.inputs[1].default_value)
        link.from_node.advance(context)
