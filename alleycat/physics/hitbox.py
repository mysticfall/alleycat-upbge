from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping

from alleycat.reactive import functions as rv
from bge.types import BL_ArmatureChannel, BL_ArmatureObject, KX_GameObject
from bpy.types import CopyLocationConstraint, CopyRotationConstraint, Object, PoseBone
from returns.curry import partial
from returns.iterables import Fold
from returns.result import ResultE, Success, safe
from rx import operators as ops

from alleycat.common import ActivatableComponent, ArgumentReader, of_type


class HitBox(ActivatableComponent[KX_GameObject]):
    class ArgKeys(ActivatableComponent.ArgKeys):
        ARMATURE: Final = "Armature"
        TARGET_BONE: Final = "Target Bone"

    args = OrderedDict(chain(ActivatableComponent.args.items(), (
        (ArgKeys.ARMATURE, Object),
        (ArgKeys.TARGET_BONE, "bone"),
    )))

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

    @property
    def processing(self) -> bool:
        return self.valid

    @property
    def armature(self) -> BL_ArmatureObject:
        return self.params["armature"]

    @property
    def channel(self) -> BL_ArmatureChannel:
        return self.params["channel"]

    @property
    def bone(self) -> PoseBone:
        return self.params["bone"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        armature = args \
            .require(self.ArgKeys.ARMATURE, Object) \
            .map(self.as_game_object) \
            .bind(safe(lambda a: of_type(a, BL_ArmatureObject))) \
            .alt(lambda a: ValueError(f"Missing or invalid armature: '{a}'."))

        bone_name = args \
            .require(self.ArgKeys.TARGET_BONE, str) \
            .alt(lambda b: ValueError(f"Missing target bone."))

        bone = bone_name.bind(lambda b: armature
                              .map(lambda a: a.blenderObject.pose.bones.get(b))
                              .bind(safe(lambda p: of_type(p, PoseBone)))
                              .alt(lambda _: ValueError(f"No such bone exists: '{b}'.")))

        channel = bone_name.bind(lambda b: armature
                                 .map(lambda a: a.channels.get(b))
                                 .bind(safe(lambda c: of_type(c, BL_ArmatureChannel)))
                                 .alt(lambda _: ValueError(f"No such channel exists: '{b}'.")))

        result = Fold.collect((
            armature.map(lambda a: ("armature", a)),
            bone.map(lambda b: ("bone", b)),
            channel.map(lambda c: ("channel", c))
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        rv.observe(self.active) \
            .pipe(ops.take_until(self.on_dispose)) \
            .subscribe(self.on_activation_change, self.error_handler)

    def on_activation_change(self, active: bool) -> None:
        if active:
            self.logger.debug("Activating ragdoll physics.")

            target = self.object.blenderObject

            for constraint in self.bone.constraints:
                constraint.mute = not (isinstance(constraint,
                                                  CopyLocationConstraint) and constraint.target is target) \
                                  and not (isinstance(constraint,
                                                      CopyRotationConstraint) and constraint.target is target)

            self.object.enableRigidBody()
        else:
            self.logger.debug("Disabling ragdoll physics.")

            self.object.disableRigidBody()

    def process(self) -> None:
        super().process()

        if not self.active:
            self.object.worldTransform = self.armature.worldTransform @ self.channel.pose_matrix
