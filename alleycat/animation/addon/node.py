from abc import abstractmethod

from bpy.types import Node

from alleycat.animation import AnimationContext
from alleycat.animation.addon import AnimationNodeTree


class AnimationNode(Node):

    @classmethod
    def poll(cls, tree: AnimationNodeTree) -> bool:
        return tree.bl_idname == AnimationNodeTree.bl_idname

    @abstractmethod
    def advance(self, context: AnimationContext) -> None:
        pass
