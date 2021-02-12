from abc import abstractmethod
from typing import Generic, List, TypeVar, cast

from bpy.types import Context, Node, NodeLink, NodeSocketStandard, UILayout

from alleycat.nodetree import BaseNode

T = TypeVar("T", covariant=True)


class ValueNode(BaseNode, Generic[T]):

    @property
    @abstractmethod
    def value(self) -> T:
        pass


class ValueSocket(NodeSocketStandard, Generic[T]):
    default_value: T

    @property
    def value(self) -> T:
        if self.is_output and self.is_linked:
            link: NodeLink = self.links[0]
            node = link.from_node

            if isinstance(node, ValueNode):
                return cast(ValueNode[T], node).value

        return self.default_value

    def draw(self, context: Context, layout: UILayout, node: Node, text: str) -> None:
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            # noinspection PyTypeChecker
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context: Context, node: Node) -> List[float]:
        return [0.631, 0.631, 0.631, 1.0]
