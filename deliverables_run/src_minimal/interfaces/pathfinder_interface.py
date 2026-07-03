from abc import ABC, abstractmethod
from typing import List, Any


class PathfinderInterface(ABC):
    @abstractmethod
    def find_path(self, start: Any, end: Any) -> List[Any]:
        """Return a list of waypoints from start to end."""
        raise NotImplementedError()
