# Student Guide: How to Explain RescueScout

## 1. Why use a Genetic Algorithm?

BFS and DFS are useful for searching a graph and finding reachable paths. This assignment asks for more than finding one path: the mission must balance target coverage, total area coverage, energy, time, and hazard exposure, while also handling several UAVs and sensor settings. A Genetic Algorithm is a suitable choice because it can improve a population of candidate plans using a score that combines these competing objectives.

The GA does not guarantee the mathematically perfect solution. It searches for a good solution, and the final result depends on the fitness weights, map, and random choices.

## 2. What is a chromosome in this project?

A chromosome represents the whole fleet's plan. There are two routes, one for each UAV, and five waypoints in each route. Each waypoint has four values:

- `x`: horizontal grid coordinate.
- `y`: vertical grid coordinate.
- `sensor_power`: 0, 1, 2, or 3. Zero switches the sensor off; higher active power gives a wider detection radius but uses more energy.
- `speed`: 1, 2, or 3. Higher speed reduces estimated flight time but increases energy cost.

So one chromosome contains `2 UAVs × 5 waypoints × 4 values = 40 values` in total.

## 3. What does the fitness function do?

A fitness function converts the mission quality into a single number. A higher score means a better plan under this simulation's priorities.

```text
fitness = 0.50 × target coverage
        + 0.15 × area coverage
        + 0.23 × (100 − energy cost score)
        + 0.05 × (100 − flight time score)
        + 0.07 × (100 − hazard exposure score)
        − constraint penalty
```

Target coverage uses the importance of each target. Area coverage is the percentage of safe grid cells reached by at least one sensor footprint. Energy and time are scaled against budgets. Hazard exposure is estimated from hazard values along the routes. No-fly-zone crossings and range violations reduce fitness.

These weights are design decisions, not universal constants. For example, increasing the target-coverage weight would tell the GA to prioritize detection more strongly, even if that increases energy use.

## 4. The GA lifecycle

1. **Initialization:** generate random chromosomes with safe waypoint coordinates.
2. **Evaluation:** calculate each chromosome's fitness.
3. **Selection:** tournament selection chooses a parent from a small random group; fitter candidates are more likely to reproduce.
4. **Crossover:** exchange a continuous section of waypoint genes between two parents.
5. **Mutation:** randomly change coordinates, sensor power (including switching the sensor off), or speed. Most coordinate changes are small moves; occasional large moves preserve exploration.
6. **Repair and penalty:** move waypoints out of no-fly cells. Penalize a route if the straight segment between two waypoints crosses a blocked cell or a drone exceeds its flight range.
7. **Elitism:** copy the two best candidates into the next generation so the best solution is not lost.
8. **Termination:** stop at the generation limit or when the best solution does not improve for 25 generations.

## 5. Which file does what?

- `uav_models.py`: defines the `Waypoint` and `Chromosome` classes.
- `environment.py`: creates the map and calculates sensor coverage and target detection.
- `genetic_algorithm.py`: contains initialization, fitness evaluation, selection, crossover, mutation, repair, and the main GA loop.
- `visualization.py`: creates the required graphs and maps.
- `main.py`: connects the pieces, runs the simulation, and saves results.

## 6. Example viva questions

**Q: Why is the problem called multi-objective?**  
Because the system must improve coverage but also reduce energy, flight time, and hazard exposure. Improving one goal can make another worse.

**Q: Why convert the objectives to one fitness score?**  
This implementation uses a weighted-sum method. It is simpler to implement and explain than a full Pareto-front algorithm, while still representing trade-offs.

**Q: What is mutation for?**  
Mutation introduces new values into the population. Without it, the population can become too similar and stop exploring useful alternatives.

**Q: What is crossover for?**  
Crossover combines parts of two parent plans, so a child can inherit useful waypoint segments from both.

**Q: Why do we need repair and penalties?**  
Repair keeps each waypoint inside the map and outside blocked cells. A penalty is still needed because two safe waypoints can be connected by a straight segment that crosses a no-fly zone. Range violations also reduce fitness.

**Q: Does the GA always find the best possible route?**  
No. It is a heuristic optimization method. It searches for a high-quality plan but does not guarantee a global optimum.

**Q: What are the figures showing?**  
The convergence plot compares best and average fitness over generations. The final route plot shows UAV trajectories over hazard zones alongside the sensor footprint heatmap. The generation snapshots compare routes and coverage early, midway, and at the end of the search.

## 7. Important limitation to mention

The project is a simplified educational simulation. It uses straight lines between waypoints and circular sensor ranges. It does not model actual drone physics, changing weather, line-of-sight, or guaranteed safe navigation around obstacles. The GA penalizes unsafe segments but does not use a separate pathfinder to route around them.


## Running the experiments for the technical report

Run `python experiments.py` from the project folder. It varies population size (30, 70, 110), mutation rate (0.05, 0.20, 0.35), and tournament size (2, 4, 8). Each setting is repeated with three random seeds. It also compares the Genetic Algorithm against Random Search using the same map, fitness function, and candidate-evaluation budget.

The plots and CSV files are saved in `output/experiments/`. The CSV files contain the raw results for your report tables. Describe the patterns your experiment actually shows; do not claim that a larger population or mutation rate always works better. Randomized algorithms can produce different results across seeds.

The fitness evaluation now includes the return leg from each UAV's final waypoint to its launch point. Energy, flight time, distance, hazard sampling, no-fly crossings, and maximum range therefore include the return trip.
