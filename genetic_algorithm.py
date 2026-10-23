"""A readable Genetic Algorithm for multi-objective UAV mission planning."""

import math
import random
from typing import Optional

from environment import GridEnvironment
from uav_models import Chromosome, Waypoint


class GeneticAlgorithm:
    """Evolve candidate UAV routes using selection, crossover, and mutation."""

    WAYPOINTS_PER_DRONE = 5
    POPULATION_SIZE = 70
    MAX_GENERATIONS = 90
    ELITE_COUNT = 2
    MAX_FLIGHT_RANGE = 60.0  # distance units per drone
    ENERGY_BUDGET = 260.0
    TIME_BUDGET = 60.0

    def __init__(
        self,
        environment: GridEnvironment,
        population_size: int = POPULATION_SIZE,
        generations: int = MAX_GENERATIONS,
        mutation_rate: float = 0.20,
        crossover_rate: float = 0.90,
        tournament_size: int = 4,
        seed: int = 21,
    ):
        self.environment = environment
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = max(1, int(tournament_size))
        self.rng = random.Random(seed)

        self.best_history: list[float] = []
        self.average_history: list[float] = []
        self.best_by_generation: list[Chromosome] = []

    def create_random_chromosome(self) -> Chromosome:
        routes = []
        for _drone in self.environment.starts:
            route = []
            for _ in range(self.WAYPOINTS_PER_DRONE):
                x, y = self.rng.choice(self.environment.free_cells)
                route.append(
                    Waypoint(
                        x=x,
                        y=y,
                        sensor_power=self.rng.randint(0, 3),
                        speed=self.rng.randint(1, 3),
                    )
                )
            routes.append(route)
        candidate = Chromosome(routes=routes)
        self.repair(candidate)
        return candidate

    def repair(self, chromosome: Chromosome) -> None:
        """Keep genes in bounds and move waypoint genes out of no-fly cells.

        Straight flight segments can still cross a no-fly zone; those violations
        receive a fitness penalty during evaluation.
        """
        for drone_index, route in enumerate(chromosome.routes):
            previous_position = self.environment.starts[drone_index]
            for waypoint in route:
                waypoint.x, waypoint.y = self.environment.nearest_free_cell(waypoint.x, waypoint.y)
                # Consecutive identical positions waste a waypoint in this model.
                if (waypoint.x, waypoint.y) == previous_position:
                    waypoint.x, waypoint.y = min(
                        (cell for cell in self.environment.free_cells if cell != previous_position),
                        key=lambda cell: (cell[0] - waypoint.x) ** 2 + (cell[1] - waypoint.y) ** 2,
                    )
                waypoint.sensor_power = max(0, min(3, int(waypoint.sensor_power)))
                waypoint.speed = max(1, min(3, int(waypoint.speed)))
                previous_position = (waypoint.x, waypoint.y)

    @staticmethod
    def sample_segment(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        """Sample grid cells along a straight segment to detect hazards/obstacles."""
        x1, y1 = start
        x2, y2 = end
        steps = max(1, int(max(abs(x2 - x1), abs(y2 - y1)) * 2))
        cells = []
        previous = None
        for step in range(steps + 1):
            fraction = step / steps
            cell = (round(x1 + (x2 - x1) * fraction), round(y1 + (y2 - y1) * fraction))
            if cell != previous:
                cells.append(cell)
                previous = cell
        return cells

    def evaluate(self, chromosome: Chromosome) -> float:
        """Evaluate coverage rewards and energy, time, risk, and constraint costs."""
        env = self.environment
        target_score, detected = env.target_coverage(chromosome)
        coverage = env.coverage_map(chromosome)
        available_cells = int((~env.blocked).sum())
        covered_cells = int(((coverage > 0) & (~env.blocked)).sum())
        area_score = 100.0 * covered_cells / available_cells if available_cells else 0.0

        total_distance = 0.0
        total_energy = 0.0
        total_time = 0.0
        hazard_samples = []
        blocked_samples = 0
        blocked_segments = 0
        total_constraint_penalty = 0.0

        for drone_index, route in enumerate(chromosome.routes):
            current = env.starts[drone_index]
            drone_distance = 0.0

            for waypoint in route:
                destination = (waypoint.x, waypoint.y)
                distance = math.hypot(destination[0] - current[0], destination[1] - current[1])
                drone_distance += distance
                total_distance += distance

                # Higher speeds cost more energy; stronger sensors also use power.
                total_energy += distance * (1.0 + 0.18 * (waypoint.speed - 1) ** 2)
                total_energy += 5.0 * waypoint.sensor_power  # 0 means the sensor is switched off.
                total_time += distance / waypoint.speed

                segment_cells = self.sample_segment(current, destination)
                segment_blocked = sum(1 for x, y in segment_cells if env.is_blocked(x, y))
                if segment_blocked:
                    blocked_segments += 1
                    blocked_samples += segment_blocked
                for x, y in segment_cells:
                    # Keep map risk in the 0..1 range, then convert to a percentage.
                    hazard_samples.append(float(env.hazard[y, x]))
                current = destination

            # Model the return flight to the drone's launch/base location.
            # The return leg uses cruise speed 2 and has no active sensor cost.
            return_speed = 2
            return_distance = math.hypot(current[0] - env.starts[drone_index][0],
                                         current[1] - env.starts[drone_index][1])
            drone_distance += return_distance
            total_distance += return_distance
            total_energy += return_distance * (1.0 + 0.18 * (return_speed - 1) ** 2)
            total_time += return_distance / return_speed

            return_cells = self.sample_segment(current, env.starts[drone_index])
            return_blocked = sum(1 for x, y in return_cells if env.is_blocked(x, y))
            if return_blocked:
                blocked_segments += 1
                blocked_samples += return_blocked
            for x, y in return_cells:
                hazard_samples.append(float(env.hazard[y, x]))

            # A range breach is penalized rather than silently ignored.
            if drone_distance > self.MAX_FLIGHT_RANGE:
                total_constraint_penalty += 2.0 * (drone_distance - self.MAX_FLIGHT_RANGE)

        # Constraint penalty discourages routes that pass through forbidden cells.
        total_constraint_penalty += 12.0 * blocked_segments + 1.5 * blocked_samples

        energy_score = min(100.0, 100.0 * total_energy / self.ENERGY_BUDGET)
        time_score = min(100.0, 100.0 * total_time / self.TIME_BUDGET)
        risk_score = 100.0 * (sum(hazard_samples) / len(hazard_samples)) if hazard_samples else 0.0

        # Weighted sum makes the trade-offs explicit and easy to explain.
        # Coverage/detection are rewards. Energy, time, and risk reduce the score.
        fitness = (
            0.50 * target_score
            + 0.15 * area_score
            + 0.23 * (100.0 - energy_score)
            + 0.05 * (100.0 - time_score)
            + 0.07 * (100.0 - risk_score)
            - total_constraint_penalty
        )

        chromosome.fitness = fitness
        chromosome.metrics = {
            "target_coverage_percent": target_score,
            "area_coverage_percent": area_score,
            "targets_detected": len(detected),
            "total_targets": len(env.targets),
            "distance": total_distance,
            "energy": total_energy,
            "flight_time": total_time,
            "hazard_exposure_percent": risk_score,
            "blocked_segments": blocked_segments,
            "blocked_samples": blocked_samples,
            "constraint_penalty": total_constraint_penalty,
        }
        return fitness

    def select_parent(
        self,
        population: list[Chromosome],
        tournament_size: Optional[int] = None,
    ) -> Chromosome:
        """Tournament selection: the fittest candidate in a random group wins."""
        size = self.tournament_size if tournament_size is None else max(1, int(tournament_size))
        contestants = self.rng.sample(population, min(size, len(population)))
        return max(contestants, key=lambda candidate: candidate.fitness)

    def crossover(self, parent_a: Chromosome, parent_b: Chromosome) -> tuple[Chromosome, Chromosome]:
        """Swap a section of waypoint genes between two parent chromosomes."""
        child_a = parent_a.clone()
        child_b = parent_b.clone()

        for drone_index in range(len(child_a.routes)):
            route_length = len(child_a.routes[drone_index])
            start = self.rng.randrange(route_length)
            end = self.rng.randint(start + 1, route_length)
            segment_a = child_a.routes[drone_index][start:end]
            segment_b = child_b.routes[drone_index][start:end]
            child_a.routes[drone_index][start:end] = segment_b
            child_b.routes[drone_index][start:end] = segment_a

        self.repair(child_a)
        self.repair(child_b)
        return child_a, child_b

    def mutate(self, chromosome: Chromosome) -> None:
        """Make small spatial changes and occasional sensor/speed changes."""
        for route in chromosome.routes:
            for waypoint in route:
                if self.rng.random() < self.mutation_rate:
                    if self.rng.random() < 0.80:
                        # Local movement explores nearby positions without a huge jump.
                        waypoint.x += self.rng.randint(-3, 3)
                        waypoint.y += self.rng.randint(-3, 3)
                    else:
                        # Occasional large move helps the population explore new areas.
                        waypoint.x, waypoint.y = self.rng.choice(self.environment.free_cells)

                if self.rng.random() < self.mutation_rate * 0.50:
                    waypoint.sensor_power += self.rng.choice([-1, 1])
                if self.rng.random() < self.mutation_rate * 0.50:
                    waypoint.speed += self.rng.choice([-1, 1])

        self.repair(chromosome)

    def run(self, patience: Optional[int] = 25) -> Chromosome:
        """Run evolution until the generation limit or no-improvement patience."""
        population = [self.create_random_chromosome() for _ in range(self.population_size)]
        for candidate in population:
            self.evaluate(candidate)

        best_ever = max(population, key=lambda candidate: candidate.fitness).clone()
        generations_without_improvement = 0

        # Generation 0 is recorded so plots show the starting population too.
        self._record_generation(population)

        for _generation in range(1, self.generations + 1):
            population.sort(key=lambda candidate: candidate.fitness, reverse=True)
            next_population = [candidate.clone() for candidate in population[:self.ELITE_COUNT]]

            while len(next_population) < self.population_size:
                parent_a = self.select_parent(population)
                parent_b = self.select_parent(population)

                if self.rng.random() < self.crossover_rate:
                    child_a, child_b = self.crossover(parent_a, parent_b)
                else:
                    child_a, child_b = parent_a.clone(), parent_b.clone()

                self.mutate(child_a)
                self.evaluate(child_a)
                next_population.append(child_a)

                if len(next_population) < self.population_size:
                    self.mutate(child_b)
                    self.evaluate(child_b)
                    next_population.append(child_b)

            population = next_population
            current_best = max(population, key=lambda candidate: candidate.fitness)
            self._record_generation(population)

            if current_best.fitness > best_ever.fitness:
                best_ever = current_best.clone()
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1

            if patience is not None and generations_without_improvement >= patience:
                break

        # Re-evaluate so returned metrics always match the returned chromosome.
        self.evaluate(best_ever)
        return best_ever

    def _record_generation(self, population: list[Chromosome]) -> None:
        scores = [candidate.fitness for candidate in population]
        best = max(population, key=lambda candidate: candidate.fitness)
        self.best_history.append(best.fitness)
        self.average_history.append(sum(scores) / len(scores))
        self.best_by_generation.append(best.clone())
