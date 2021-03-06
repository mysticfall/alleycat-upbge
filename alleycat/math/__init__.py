from validator_collection import validators


def normalize_euler(angle: float) -> float:
    angle = validators.float(angle) % 360

    if angle > 180:
        angle -= 360

    return angle
