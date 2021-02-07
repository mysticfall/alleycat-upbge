from bpy.types import Context, NodeLink

from alleycat.animation import AnimationContext
from alleycat.animation.addon import AnimationNode, NodeSocketAnimation


class AnimationOutputNode(AnimationNode):
    bl_idname: str = "alleycat.animation.addon.AnimationOutputNode"

    bl_label: str = "Animation Output"

    bl_icon: str = "ACTION"

    def init(self, context: Context) -> None:
        self.inputs.new(NodeSocketAnimation.bl_idname, "Input").hide_value = True
        print("### INIT!!")

    def advance(self, context: AnimationContext) -> None:
        link: NodeLink = self.inputs[0].links[0]
        link.from_node.advance(context)

    def update(self) -> None:
        super().update()
        print("### UPDATE!!")
