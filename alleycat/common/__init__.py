from .exceptions import InvalidTypeError, IllegalStateError, AlreadyDisposedError
from .validators import of_type
from .initializable import Initializable, AlreadyInitializedError
from .math import clamp, normalize_angle, normalize_euler
from .lookup import Lookup
from .arguments import ArgumentReader
from .component import BaseComponent, IDComponent, NotStartedError, find_component, require_component
from .activatable import Activatable, ActivatableComponent
from .entity import Entity

# TODO: Use 'Final' when UPBGE's default Python distribution updates to 3.8+.
ConfigMetaSchema = "http://json-schema.org/draft-07/schema#"
