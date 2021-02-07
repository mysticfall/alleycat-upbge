from typing import Sequence, Set, Type

from bpy.utils import register_class, unregister_class
from nodeitems_utils import NodeItem, register_node_categories, unregister_node_categories

from alleycat.animation.addon import AnimationNodeCategory, AnimationNodeTree, AnimationOutputNode, MixAnimationNode, \
    NodeSocketAnimation, PlayActionNode
from alleycat.common import NodeSocketFloat0To1

bl_info = {
    "name": "AlleyCat Framework",
    "description": "Programmer friendly framework for UPBGE game engine.",
    "category": "Game Engine",
    "author": "Xavier Cho",
    "version": (0, 1),
    "blender": (2, 93, 0),
    "wiki_url": "https://github.com/mysticfall/alleycat",
    "tracker_url": "https://github.com/mysticfall/alleycat/issues",
    "support": "COMMUNITY"
}

CustomTypes: Set[Type] = {
    AnimationNodeTree,
    PlayActionNode,
    MixAnimationNode,
    AnimationOutputNode,
    NodeSocketAnimation,
    NodeSocketFloat0To1
}

NodeCategories: Sequence[AnimationNodeCategory] = (
    AnimationNodeCategory("ANIMATION_NODES", "Animation", items=[
        NodeItem(PlayActionNode.bl_idname),
        NodeItem(MixAnimationNode.bl_idname),
        NodeItem(AnimationOutputNode.bl_idname),
    ]),
)


def register() -> None:
    for t in CustomTypes:
        register_class(t)

    register_node_categories("ANIMATION_NODES", NodeCategories)


def unregister() -> None:
    unregister_node_categories("ANIMATION_NODES")

    for t in CustomTypes:
        unregister_class(t)


if __name__ == "__main__":
    register()
