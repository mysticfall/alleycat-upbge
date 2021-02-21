from typing import Optional

from bpy.props import PointerProperty
from bpy.types import Action, Context, NodeLink, UILayout
from returns.maybe import Maybe, Nothing, Some
from validator_collection import validators

from alleycat.animation import AnimationResult, Animator, PlayMode
from alleycat.animation.addon import AnimationNode, NodeSocketAnimation
from alleycat.nodetree import NodeSocketFloat, NodeSocketFloat0, NodeSocketFloat0To1


class PlayActionNode(AnimationNode):
    bl_idname: str = "alleycat.animation.addon.PlayActionNode"

    bl_label: str = "Play Action"

    bl_icon: str = "ACTION"

    action: PointerProperty(name="Action", type=Action, options={"LIBRARY_EDITABLE"})  # type:ignore

    _result: Maybe[AnimationResult] = Nothing

    # noinspection PyUnusedLocal
    def init(self, context: Optional[Context]) -> None:
        self.inputs.new(NodeSocketFloat0To1.bl_idname, "Speed")
        self.inputs.new(NodeSocketFloat0.bl_idname, "Blend")

        self.outputs.new(NodeSocketAnimation.bl_idname, "Output")

    @property
    def speed(self) -> float:
        return self.inputs["Speed"].value

    @property
    def blend(self) -> float:
        return self.inputs["Blend"].value

    # noinspection PyMethodMayBeStatic
    @property
    def depth(self) -> int:
        return 1

    @property
    def last_frame(self) -> int:
        return self.attrs["last_frame"] if "last_frame" in self.attrs else 0

    @last_frame.setter
    def last_frame(self, value: int) -> None:
        self.attrs["last_frame"] = validators.float(value, minimum=0.0)

    def insert_link(self, link: NodeLink) -> None:
        assert link

        if link.to_node != self:
            return

        link.is_valid = isinstance(link.from_socket, NodeSocketFloat)

    def draw_buttons(self, context: Context, layout: UILayout) -> None:
        assert context
        assert layout

        layout.prop(self, "action")

    def advance(self, animator: Animator) -> Maybe[AnimationResult]:
        if self._result == Nothing:
            result = AnimationResult()
            self._result = Some(result)
        else:
            result = self._result.unwrap()
            result.reset()

        if not self.action:
            return Nothing

        fps = 24.0
        total = self.action.frame_range[-1]

        start_frame = self.last_frame if self.last_frame < total and animator.weight < 1 else 0
        end_frame = min(start_frame + animator.time_delta * fps, total)

        self.last_frame = end_frame

        group = self.action.groups.get("root")

        for i in range(3):
            channel = group.channels[i]
            result.offset[channel.array_index] = channel.evaluate(start_frame)

        animator.play(self.action, start_frame=start_frame, end_frame=end_frame, play_mode=PlayMode.Play)

        return self._result
