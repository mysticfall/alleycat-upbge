from typing import Optional, cast

from bpy.types import Context, NodeLink, NodeSocket
from returns.maybe import Maybe, Nothing
from validator_collection import not_empty

from alleycat.animation import AnimationContext
from alleycat.animation.addon import AnimationNode, NodeSocketAnimation
from alleycat.nodetree import NodeSocketFloat, NodeSocketFloat0To1


class MixAnimationNode(AnimationNode):
    bl_idname: str = "alleycat.animation.addon.MixAnimationNode"

    bl_label: str = "Mix"

    bl_icon: str = "ACTION"

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

    def advance(self, context: AnimationContext) -> None:
        self.input1.map(lambda i1: self.input2.map(lambda i2: self.process(i1, i2, context)))

    def process(self, input1: AnimationNode, input2: AnimationNode, context: AnimationContext) -> None:
        not_empty(input1)
        not_empty(input2)

        not_empty(context)

        context.weight = self.mix

        input1.advance(context)

        context.layer -= input1.depth
        context.weight = 1.0 - self.mix

        input2.advance(context)
