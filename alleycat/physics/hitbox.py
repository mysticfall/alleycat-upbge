from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping, Sequence

from alleycat.reactive import functions as rv
from bge.types import BL_ArmatureChannel, BL_ArmatureObject, KX_GameObject
from bpy.types import Constraint, CopyLocationConstraint, CopyRotationConstraint, Object, PoseBone
from returns.curry import partial
from returns.iterables import Fold
from returns.result import ResultE, Success, safe
from rx import operators as ops
from validator_collection import not_empty

from alleycat.common import ArgumentReader, clamp, of_type
from alleycat.game import BaseComponent


class ConstraintControl:
    def __init__(self, constraint: Constraint, binding: bool = True) -> None:
        self._constraint = not_empty(constraint)

        self._binding = binding
        self._init_value = constraint.influence

        if binding:
            self._weight = 0.0 if constraint.mute else constraint.influence
        else:
            self._weight = constraint.influence if constraint.mute else 0.0

    @property
    def constraint(self) -> Constraint:
        return self._constraint

    @property
    def binding(self) -> bool:
        return self._binding

    @property
    def init_value(self) -> float:
        return self._init_value

    @property
    def weight(self) -> float:
        return self._weight

    @weight.setter
    def weight(self, value: float) -> None:
        self._weight = clamp(value, 0.0, 1.0)

        if self.binding:
            influence = self.init_value * value
            self.constraint.mute = influence == 0.0 or value == 0.0
        else:
            influence = self.init_value * (1.0 - value)
            self.constraint.mute = influence == 0.0 or value == 1.0

        self.constraint.influence = influence

    def __repr__(self) -> str:
        return self.constraint.name


class HitBox(BaseComponent[KX_GameObject]):
    class ArgKeys(BaseComponent.ArgKeys):
        ARMATURE: Final = "Armature"
        TARGET_BONE: Final = "Target Bone"

    args = OrderedDict(chain(BaseComponent.args.items(), (
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

    @property
    def controls(self) -> Sequence[ConstraintControl]:
        return self.params["controls"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        # noinspection PyTypeChecker
        armature = args \
            .require(HitBox.ArgKeys.ARMATURE, Object) \
            .map(self.as_game_object) \
            .bind(safe(lambda a: of_type(a, BL_ArmatureObject))) \
            .alt(lambda a: ValueError(f"Missing or invalid armature: '{a}'."))

        bone_name = args \
            .require(HitBox.ArgKeys.TARGET_BONE, str) \
            .alt(lambda b: ValueError("Missing target bone."))

        bone = bone_name.bind(lambda b: armature
                              .map(lambda a: a.blenderObject.pose.bones.get(b))
                              .bind(safe(lambda p: of_type(p, PoseBone)))
                              .alt(lambda _: ValueError(f"No such bone exists: '{b}'.")))

        # noinspection PyUnresolvedReferences
        bl_object = self.object.blenderObject

        def is_hitbox_binding(c: Constraint) -> bool:
            is_type = partial(isinstance, c)
            is_copy_type = (is_type(CopyLocationConstraint) or is_type(CopyRotationConstraint))

            return is_copy_type and getattr(c, "target") is bl_object

        def create_control(c: Constraint) -> ConstraintControl:
            return ConstraintControl(c, is_hitbox_binding(c))

        controls = bone.map(lambda b: tuple(map(create_control, b.constraints)))

        channel = bone_name.bind(lambda b: armature
                                 .map(lambda a: a.channels.get(b))
                                 .bind(safe(lambda c: of_type(c, BL_ArmatureChannel)))
                                 .alt(lambda _: ValueError(f"No such channel exists: '{b}'.")))

        result = Fold.collect((
            armature.map(lambda a: ("armature", a)),
            bone.map(lambda b: ("bone", b)),
            channel.map(lambda c: ("channel", c)),
            controls.map(lambda c: ("controls", c))
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        rv.observe(self.active) \
            .pipe(ops.take_until(self.on_dispose)) \
            .subscribe(self.on_activation_change, self.error_handler)

        super().initialize()

    def on_activation_change(self, active: bool) -> None:
        if active:
            self.logger.debug("Activating ragdoll physics.")

            for c in self.controls:
                c.weight = 1.0

            self.object.enableRigidBody()
        else:
            self.logger.debug("Disabling ragdoll physics.")

            for c in self.controls:
                c.weight = 0.0

            self.object.disableRigidBody()

    def process(self) -> None:
        super().process()

        if not self.active:
            # noinspection PyUnresolvedReferences
            self.object.worldTransform = self.armature.worldTransform @ self.channel.pose_matrix
