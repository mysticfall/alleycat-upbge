class InvalidTypeError(ValueError):
    pass


class IllegalStateError(Exception):
    pass


class AlreadyDisposedError(IllegalStateError):
    pass
