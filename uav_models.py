"""Data structures used by the RescueScout UAV Genetic Algorithm project."""

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any


@dataclass
class Waypoint:
    """One planned stop, including sensor power and flight speed settings."""

    x: int
    y: int
    sensor_power: int  # 1 = low, 2 = medium, 3 = high
    speed: int         # 1 = slow, 2 = normal, 3 = fast


@dataclass
class Chromosome:
    """A candidate mission plan for the whole UAV fleet.

    routes[drone_number] is a list of waypoints for that drone. Each waypoint
    stores (x, y, sensor_power, speed), so the chromosome encodes both paths
    and some operational settings.
    """

    routes: list[list[Waypoint]]
    fitness: float = float("-inf")
    metrics: dict[str, Any] = field(default_factory=dict)

    def clone(self) -> "Chromosome":
        """Return an independent copy for selection and genetic operations."""
        return deepcopy(self)
