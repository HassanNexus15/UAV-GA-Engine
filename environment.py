"""Create and manage the simulated disaster grid."""

import math
import numpy as np


class GridEnvironment:
    """A 2D map containing no-fly cells, hazards, targets, and UAV bases."""

    def __init__(self, width: int = 20, height: int = 20, seed: int = 7):
        self.width = width
        self.height = height
        rng = np.random.default_rng(seed)

        # True means that a cell is a hard obstacle / no-fly zone.
        self.blocked = np.zeros((height, width), dtype=bool)
        self.blocked[5:9, 6:9] = True
        self.blocked[11:14, 12:15] = True
        self.blocked[3:5, 13:17] = True
        self.blocked[15:18, 3:5] = True

        # Hazard values range from 0 (low) to 1 (very hazardous).
        self.hazard = rng.uniform(0.02, 0.22, size=(height, width))
        yy, xx = np.mgrid[0:height, 0:width]
        hazard_pockets = [
            (8, 13, 0.75, 2.7),
            (15, 9, 0.65, 2.3),
            (3, 6, 0.55, 2.0),
        ]
        for cx, cy, strength, spread in hazard_pockets:
            pocket = strength * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * spread ** 2))
            self.hazard += pocket
        self.hazard = np.clip(self.hazard, 0.0, 1.0)

        # Target format: (x, y, importance). Higher importance earns more reward.
        self.targets = [
            (4, 15, 3),
            (6, 17, 2),
            (10, 14, 3),
            (14, 16, 3),
            (16, 12, 2),
            (5, 8, 2),
            (12, 7, 3),
            (17, 5, 2),
        ]
        # Start/base locations for two drones.
        self.starts = [(1, 1), (18, 1)]

        # Safety checks protect the simulation if map settings are edited later.
        for x, y, _ in self.targets:
            self.blocked[y, x] = False
        for x, y in self.starts:
            self.blocked[y, x] = False

        self.free_cells = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if not self.blocked[y, x]
        ]

    def is_blocked(self, x: int, y: int) -> bool:
        """Return True if a coordinate is outside the map or blocked."""
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        return bool(self.blocked[y, x])

    def nearest_free_cell(self, x: int, y: int) -> tuple[int, int]:
        """Repair a waypoint by moving it to the nearest safe grid cell."""
        x = max(0, min(self.width - 1, int(x)))
        y = max(0, min(self.height - 1, int(y)))
        if not self.is_blocked(x, y):
            return x, y
        return min(self.free_cells, key=lambda cell: (cell[0] - x) ** 2 + (cell[1] - y) ** 2)

    def coverage_map(self, chromosome) -> np.ndarray:
        """Return how many sensor footprints cover each map cell."""
        coverage = np.zeros((self.height, self.width), dtype=int)
        yy, xx = np.mgrid[0:self.height, 0:self.width]
        radius_by_power = {0: 0.0, 1: 1.8, 2: 2.8, 3: 3.8}

        for route in chromosome.routes:
            for waypoint in route:
                if waypoint.sensor_power == 0:
                    continue  # Sensor is switched off at this waypoint.
                radius = radius_by_power[waypoint.sensor_power]
                footprint = (xx - waypoint.x) ** 2 + (yy - waypoint.y) ** 2 <= radius ** 2
                footprint &= ~self.blocked
                coverage[footprint] += 1
        return coverage

    def target_coverage(self, chromosome) -> tuple[float, set[int]]:
        """Return priority-weighted target coverage (0-100) and detected IDs."""
        radius_by_power = {0: 0.0, 1: 1.8, 2: 2.8, 3: 3.8}
        detected = set()
        total_priority = sum(priority for _, _, priority in self.targets)

        for target_id, (tx, ty, _priority) in enumerate(self.targets):
            for route in chromosome.routes:
                for waypoint in route:
                    if waypoint.sensor_power == 0:
                        continue
                    radius = radius_by_power[waypoint.sensor_power]
                    if math.hypot(tx - waypoint.x, ty - waypoint.y) <= radius:
                        detected.add(target_id)
                        break
                if target_id in detected:
                    break

        detected_priority = sum(self.targets[i][2] for i in detected)
        score = 100.0 * detected_priority / total_priority if total_priority else 0.0
        return score, detected
