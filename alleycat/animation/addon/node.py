from abc import abstractmethod

from alleycat.animation import AnimationContext, AnimationLoopAware
from alleycat.animation.addon import AnimationNodeTree
from alleycat.nodetree import BaseNode


class AnimationNode(AnimationLoopAware, BaseNode[AnimationContext]):

    @classmethod
    def poll(cls, tree: AnimationNodeTree) -> bool:
        return tree.bl_idname == AnimationNodeTree.bl_idname

    @abstractmethod
    def depth(self) -> int:
        pass

    @abstractmethod
    def advance(self, context: AnimationContext) -> None:
        pass
