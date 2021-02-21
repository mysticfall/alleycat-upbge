from typing import List, cast

from bpy.types import Context, Node, NodeSocketStandard, UILayout
from mathutils import Vector
from nodeitems_utils import NodeCategory
from returns.maybe import Maybe, Nothing, Some
from validator_collection import not_empty

from alleycat.animation import AnimationContext, AnimationLoopAware
from alleycat.nodetree import BaseNodeTree


class AnimationNodeTree(AnimationLoopAware, BaseNodeTree[AnimationContext]):
    bl_idname: str = "alleycat.animation.addon.AnimationNodeTree"

    bl_label: str = "AlleyCat Animation"

    bl_description: str = "Animation node tree for AlleyCat framework."

    bl_icon: str = "NODETREE"

    _output: Maybe[AnimationLoopAware] = Nothing

    def validate(self) -> bool:
        if not super().validate():
            return False

        try:
            from .output import AnimationOutputNode

            # noinspection PyTypeChecker
            node = next(filter(lambda n: isinstance(n, AnimationOutputNode), self.nodes))

            self._output = Some(cast(AnimationLoopAware, node))

            self.logger.debug("Using output node: %s.", node)
        except StopIteration:
            self.logger.warning("Animation tree does not have a valid output node.")

            self._output = Nothing

        return self.output != Nothing

    @property
    def output(self) -> Maybe[AnimationLoopAware]:
        return self._output

    def advance(self, context: AnimationContext) -> None:
        return self.output.map(lambda o: o.advance(not_empty(context))).value_or(Vector((0, 0, 0)))


class AnimationNodeCategory(NodeCategory):

    @classmethod
    def poll(cls, context: Context) -> bool:
        assert context

        return context.space_data.tree_type == AnimationNodeTree.bl_idname


class NodeSocketAnimation(NodeSocketStandard):
    bl_idname: str = "alleycat.animation.addon.NodeSocketAnimation"

    def draw(self, context: Context, layout: UILayout, node: Node, text: str) -> None:
        assert context
        assert layout
        assert node
        assert text

        layout.label(text=text)

    def draw_color(self, context: Context, node: Node) -> List[float]:
        assert context
        assert node

        return [0.388, 0.780, 0.388, 1.0]
