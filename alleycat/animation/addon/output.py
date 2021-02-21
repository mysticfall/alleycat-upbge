from typing import Optional, cast

from bpy.types import Context, NodeLink
from returns.maybe import Maybe, Nothing
from validator_collection import not_empty

from alleycat.animation import AnimationResult, Animator
from alleycat.animation.addon import AnimationNode, NodeSocketAnimation


class AnimationOutputNode(AnimationNode):
    bl_idname: str = "alleycat.animation.addon.AnimationOutputNode"

    bl_label: str = "Animation Output"

    bl_icon: str = "ACTION"

    # noinspection PyUnusedLocal
    def init(self, context: Optional[Context]) -> None:
        self.inputs.new(NodeSocketAnimation.bl_idname, "Input").hide_value = True

    @property
    def input(self) -> Maybe[AnimationNode]:
        return self.attrs["input"] if "input" in self.attrs else Nothing

    @property
    def depth(self) -> int:
        return self.input.map(lambda i: i.depth).value_or(0)

    def validate(self) -> bool:
        if not super().validate():
            return False

        node: Maybe[AnimationNode] = Nothing

        if len(self.inputs[0].links) > 0:
            input_link: NodeLink = self.inputs[0].links[0]

            if isinstance(input_link.from_socket, NodeSocketAnimation):
                node = Maybe.from_optional(input_link.from_node).map(lambda n: cast(AnimationNode, n))
            else:
                input_link.is_valid = False

            for link in self.inputs[0].links[1:]:
                link.is_valid = False

        self.attrs["input"] = node

        self.logger.info("Using input node: %s.", node)

        return self.input != Nothing

    def insert_link(self, link: NodeLink) -> None:
        assert link
        assert link.to_node == self

        link.is_valid = isinstance(link.from_socket, NodeSocketAnimation)

    def advance(self, animator: Animator) -> Maybe[AnimationResult]:
        not_empty(animator)

        animator.layer = self.depth

        return self.input.bind(lambda i: i.advance(not_empty(animator)))
