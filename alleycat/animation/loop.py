from abc import abstractmethod

from alleycat.animation import AnimationResult, Animator


# We can't make it an actual abstract type (i.e. ABC) as it will complicate things when
# extended by Node and NodeTree. Yet another reason why type hinting in Python is nothing
# more than a toy *shrug*.
class AnimationLoopAware:

    @abstractmethod
    def advance(self, animator: Animator) -> AnimationResult:
        pass
