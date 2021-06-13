from typing import Optional, cast

from bpy.props import EnumProperty
from bpy.types import Context, NodeLink, NodeSocket, UILayout
from returns.maybe import Maybe, Nothing
from validator_collection import not_empty

from alleycat.animation import AnimationResult, Animator, BlendMode
from alleycat.animation.addon import AnimationNode, NodeSocketAnimation
from alleycat.nodetree import NodeSocketFloat, NodeSocketFloat0To1


class MixAnimationNode(AnimationNode):
    bl_idname: str = "alleycat.animation.addon.MixAnimationNode"

    bl_label: str = "Mix"

    bl_icon: str = "ACTION"

    # noinspection PyTypeChecker
    blend_mode: EnumProperty(  # type:ignore
        name="Blend Mode",
        items=[("blend", "Blend", ""), ("add", "Add", "")],
        options={"LIBRARY_EDITABLE"})

    _result: Optional[AnimationResult] = None

    # noinspection PyUnusedLocal
    def init(self, context: Optional[Context]) -> None:
        self.inputs.new(NodeSocketFloat0To1.bl_idname, "Mix")

        self.inputs.new(NodeSocketAnimation.bl_idname, "Input")
        self.inputs.new(NodeSocketAnimation.bl_idname, "Input")

        self.outputs.new(NodeSocketAnimation.bl_idname, "Output")

    @property
    def mix(self) -> float:
        return self.inputs["Mix"].value

    @property
    def input1(self) -> Maybe[AnimationNode]:
        return self.attrs["input1"] if "input1" in self.attrs else Nothing

    @property
    def input2(self) -> Maybe[AnimationNode]:
        return self.attrs["input2"] if "input2" in self.attrs else Nothing

    @property
    def depth(self) -> int:
        return self.input1.map(lambda i: i.depth).value_or(0) + self.input2.map(lambda i: i.depth).value_or(0)

    def validate(self) -> bool:
        if not super().validate():
            return False

        def validate_input(attr: str, socket: NodeSocket):
            node: Maybe[AnimationNode] = Nothing

            if len(socket.links) > 0:
                input_link: NodeLink = socket.links[0]

                if isinstance(input_link.from_socket, NodeSocketAnimation):
                    node = Maybe.from_optional(input_link.from_node).map(lambda n: cast(AnimationNode, n))
                else:
                    input_link.is_valid = False

                for link in socket.links[1:]:
                    link.is_valid = False

            self.attrs[attr] = node
            self.logger.info("Using input node for %s: %s.", attr, node)

            return node != Nothing

        return validate_input("input1", self.inputs[1]) and validate_input("input2", self.inputs[2])

    def insert_link(self, link: NodeLink) -> None:
        assert link

        if link.to_node != self:
            return

        if link.to_socket.name == "Mix":
            link.is_valid = isinstance(link.from_socket, NodeSocketFloat)
        elif link.to_socket.name == "Input":
            link.is_valid = isinstance(link.from_socket, NodeSocketAnimation)
        else:
            link.is_valid = False

    def draw_buttons(self, context: Context, layout: UILayout) -> None:
        assert context
        assert layout

        layout.prop(self, "blend_mode")

    def advance(self, animator: Animator) -> AnimationResult:
        return self.input1 \
            .bind(lambda i1: self.input2.map(lambda i2: self.process(i1, i2, animator))) \
            .or_else_call(AnimationResult)

    def process(self, input1: AnimationNode, input2: AnimationNode, animator: Animator) -> AnimationResult:
        not_empty(input1)
        not_empty(input2)

        not_empty(animator)

        if self._result:
            self._result.reset()
        else:
            self._result = AnimationResult()

        animator.weight = self.mix
        animator.blend_mode = BlendMode.Add if self.blend_mode == "add" else BlendMode.Blend

        result1 = input1.advance(animator)

        animator.layer -= input1.depth
        animator.weight = 1.0 - self.mix

        result2 = input2.advance(animator)

        return self._merge_result(result1, result2)

    def _merge_result(self, r1: AnimationResult, r2: AnimationResult) -> AnimationResult:
        assert self._result

        result = self._result.copy(r1)

        result.offset = r1.offset * (1 - self.mix) + r2.offset * self.mix

        return result
