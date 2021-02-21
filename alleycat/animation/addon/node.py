from abc import abstractmethod

from returns.maybe import Maybe

from alleycat.animation import AnimationLoopAware, AnimationResult, Animator
from alleycat.animation.addon import AnimationNodeTree
from alleycat.nodetree import BaseNode


class AnimationNode(AnimationLoopAware, BaseNode):

    @classmethod
    def poll(cls, tree: AnimationNodeTree) -> bool:
        return tree.bl_idname == AnimationNodeTree.bl_idname

    @abstractmethod
    def depth(self) -> int:
        pass

    @abstractmethod
    def advance(self, animator: Animator) -> Maybe[AnimationResult]:
        pass
