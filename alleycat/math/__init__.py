import math

from validator_collection import validators


def normalize_angle(angle: float) -> float:
    angle = validators.float(angle) % (math.pi * 2)

    if angle > math.pi:
        angle -= math.pi * 2

    return angle


def normalize_euler(angle: float) -> float:
    angle = validators.float(angle) % 360

    if angle > 180:
        angle -= 360

    return angle


def clamp(value: float, min_value: float, max_value: float) -> float:
    return min(max(validators.float(value), validators.float(min_value)),
               validators.float(max_value, minimum=min_value))
