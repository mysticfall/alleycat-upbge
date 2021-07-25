from typing import Final

from .exceptions import InvalidTypeError, IllegalStateError, AlreadyDisposedError
from .validators import of_type
from .initializable import Initializable, AlreadyInitializedError
from .math import clamp, normalize_angle, normalize_euler
from .lookup import Lookup
from .arguments import ArgumentReader

ConfigMetaSchema: Final = "http://json-schema.org/draft-07/schema#"
