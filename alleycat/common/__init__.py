from .validators import validate_type
from .exceptions import InvalidTypeError
from .validators import validate_type
from .math import clamp, normalize_angle, normalize_euler
from .lookup import Lookup
from .arguments import ArgumentReader
from .component import BaseComponent, IDComponent
from .activatable import Activatable, ActivatableComponent

# TODO: Use 'Final' when UPBGE's default Python distribution updates to 3.8+.
ConfigMetaSchema = "http://json-schema.org/draft-07/schema#"
