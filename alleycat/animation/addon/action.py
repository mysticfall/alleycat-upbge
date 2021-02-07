from bpy.props import PointerProperty
from bpy.types import Action, Context, UILayout

from alleycat.animation import AnimationContext, PlayMode
from alleycat.animation.addon import AnimationNode, NodeSocketAnimation
from alleycat.common import NodeSocketFloat0To1


class PlayActionNode(AnimationNode):
    bl_idname: str = "alleycat.animation.addon.PlayActionNode"

    bl_label: str = "Play Action"

    bl_icon: str = "ACTION"

    action: PointerProperty(name="Action", type=Action, options={"LIBRARY_EDITABLE"})  # type:ignore

    def init(self, context: Context) -> None:
        self.inputs.new(NodeSocketFloat0To1.bl_idname, "Speed")
        self.inputs.new(NodeSocketFloat0To1.bl_idname, "Blend")

        self.outputs.new(NodeSocketAnimation.bl_idname, "Output")

    def draw_buttons(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, "action")

    def advance(self, context: AnimationContext) -> None:
        print(context.action)

        if not context.playing:
            context.play(self.action, play_mode=PlayMode.Loop)
