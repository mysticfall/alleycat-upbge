from abc import abstractmethod
from typing import Any, Dict, cast

from bpy.types import Node, NodeTree
from validator_collection import not_empty

from alleycat.log import LoggingSupport


class NodeStructure(LoggingSupport):

    @property
    @abstractmethod
    def valid(self) -> bool:
        pass

    @valid.setter
    def valid(self, value: bool) -> None:
        pass

    def start(self) -> None:
        self.valid = self.validate()

        self.logger.info("Node has started (valid: %s).", self.valid)

    def validate(self) -> bool:
        return True

    def update(self) -> None:
        self.logger.debug("Node structure is updated.")

        self.valid = self.validate()


class BaseNode(NodeStructure, Node):
    _attributes: Dict[int, Dict[str, Any]] = dict()

    @property
    def logger_name(self) -> str:
        return ".".join((super().logger_name, self.name))

    @property
    def valid(self) -> bool:
        return self.attrs["valid"]

    @valid.setter
    def valid(self, value: bool) -> None:
        self.attrs["valid"] = value

    @property
    def attrs(self) -> Dict[str, Any]:
        key = hash(self)

        if key not in self._attributes:
            attributes: Dict[str, Any] = dict()
            self._attributes[key] = attributes
        else:
            attributes = self._attributes[key]

        return attributes

    def copy(self, node: Node) -> None:
        if not isinstance(not_empty(node), BaseNode):
            raise ValueError(f"The specified argument is not an instance of BaseNode: {node}.")

        self._attributes[hash(self)] = cast(BaseNode, node).attrs

    def free(self) -> None:
        key = hash(self)

        if key in self._attributes:
            del self._attributes[key]


class BaseNodeTree(NodeStructure, NodeTree):
    _valid: bool = False

    @property
    def valid(self) -> bool:
        return self._valid

    @valid.setter
    def valid(self, value: bool) -> None:
        self._valid = value

    def validate(self) -> bool:
        # noinspection PyTypeChecker
        tuple(map(self.links.remove, filter(lambda l: not l.is_valid, self.links)))

        return super().validate()

    def start(self) -> None:
        super().start()

        for node in self.nodes:
            cast(NodeStructure, node).start()
