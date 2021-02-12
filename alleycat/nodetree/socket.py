from bpy.props import FloatProperty

from alleycat.nodetree import ValueSocket


class NodeSocketFloat(ValueSocket[float]):
    pass


class NodeSocketFloat0(NodeSocketFloat):
    bl_idname: str = "alleycat.nodetree.NodeSocketFloat0"

    default_value: FloatProperty(name="Value", default=0.0, min=0.0)  # type:ignore


class NodeSocketFloat0To1(NodeSocketFloat):
    bl_idname: str = "alleycat.nodetree.NodeSocketFloat0To1"

    default_value: FloatProperty(name="Value", default=1.0, min=0.0, max=1.0)  # type:ignore
