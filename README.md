# RescueScout: UAV Disaster Survey Strategy Engine

RescueScout is an educational Artificial Intelligence project that uses a **Genetic Algorithm (GA)** to plan survey missions for two Unmanned Aerial Vehicles (UAVs). The simulation uses a 20 x 20 grid, priority targets, hazard pockets, and no-fly cells. The GA evolves waypoints, sensor power, and speed settings while balancing coverage against energy use, flight time, and risk.

This version is intentionally built with beginner-to-intermediate Python concepts: classes, lists, loops, functions, `random`, NumPy arrays, and Matplotlib plots.

## Features

- Two UAVs with separate starting locations and five waypoints each.
- Each waypoint stores an `(x, y)` coordinate, sensor power (0–3), and speed (1–3).
- Target zones have priorities, so high-priority targets contribute more to the coverage reward.
- Hazard values are simulated with several high-risk pockets.
- No-fly cells are repaired when a waypoint lands inside an obstacle; line segments that cross no-fly cells receive a fitness penalty.
- Maximum flight range is checked for each drone.
- Tournament selection, segment-swapping crossover, spatial mutation, and elitism.
- A weighted fitness function balances coverage, energy, flight time, and risk.
- Early stopping ends the run if the best solution fails to improve for a set number of generations.
- Plots show fitness convergence, the best routes and coverage heatmap, and snapshots from different generations.

## Project files

```text
rescue_scout/
├── main.py                  # Run the complete simulation
├── environment.py           # Grid, targets, hazards, obstacles, coverage map
├── uav_models.py            # Waypoint and Chromosome classes
├── genetic_algorithm.py     # Fitness, selection, crossover, mutation, GA loop
├── visualization.py         # Required plots
├── experiments.py           # Sensitivity tests and GA vs Random Search
├── requirements.txt         # Python dependencies
├── README.md
└── output/
    ├── ...                  # Main simulation plots and summary
    └── experiments/         # Experiment plots and CSV results
```

## Requirements

- Python 3.10 or newer
- NumPy
- Matplotlib

## How to run

Open a terminal inside the `rescue_scout` folder.

### 1. Create a virtual environment (recommended)

Windows:

```bash
py -m venv .venv
.venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install packages

```bash
python -m pip install -r requirements.txt
```

### 3. Run the simulation

```bash
python main.py
```

The program prints the best mission's metrics and saves these files to `output/`:

- `fitness_convergence.png` — best and average fitness over generations.
- `best_routes_and_coverage.png` — final UAV paths plus a sensor coverage heatmap.
- `generation_snapshots.png` — route and coverage comparisons at the start, middle, and end of evolution.
- `run_summary.txt` — mission metrics and waypoint settings.

The random seeds are fixed so the demo is reproducible. Each UAV's evaluated route includes its return trip to its launch point. The route plots also show this return leg.

### Run the experiments for the technical report

After the regular simulation, run the experiment script from the same project folder:

```bash
python experiments.py
```

The script performs three sensitivity experiments and a baseline comparison. It repeats every sensitivity setting with three random seeds and varies one parameter at a time:

- Population size: 30, 70, and 110.
- Mutation rate: 0.05, 0.20, and 0.35.
- Tournament size: 2, 4, and 8 (higher values normally mean stronger selection pressure).
- Genetic Algorithm versus Random Search: three paired trials using the same grid and fitness function and the same number of candidate evaluations per pair.

Experiment plots and data are saved to `output/experiments/`. The folder includes four PNG charts plus CSV files with each trial's metrics and the baseline convergence curves. Use these measured results in the technical report rather than inventing or estimating experiment outcomes.

Experiment settings such as seed count and generation count can be changed near the top of `experiments.py`. For the baseline comparison, the Genetic Algorithm runs for its full configured generation count so it can be compared using an equal candidate-evaluation budget.

## How the Genetic Algorithm works

1. **Initialize:** create a population of random mission plans. Every chromosome contains two routes. Each route has five waypoint genes.
2. **Evaluate:** calculate a fitness score for each chromosome.
3. **Select:** tournament selection picks fitter candidates as parents.
4. **Crossover:** for each drone, exchange a continuous section of waypoints between two parents.
5. **Mutate:** sometimes move a waypoint, change sensor power, or change speed.
6. **Repair:** keep waypoint coordinates inside the map and move any waypoint out of a no-fly cell.
7. **Repeat:** preserve the best two solutions (elitism), create the next population, and stop after the generation limit or a period without improvement.

## Chromosome representation

One chromosome represents both UAV missions. Conceptually, it looks like this:

```text
Chromosome
├── UAV 1: [(x, y, sensor, speed), ... five waypoints ...]
└── UAV 2: [(x, y, sensor, speed), ... five waypoints ...]
```

Sensor power controls the simulated detection radius: power 0 switches the sensor off, power 1 has the smallest active radius, and power 3 has the largest radius. Higher active sensor power costs more energy. The speed value determines the speed used for the segment ending at that waypoint; faster travel reduces estimated flight time but increases energy expenditure.

## Fitness function

The program uses a weighted single score to represent the competing objectives:

```text
fitness = 0.50 * target_coverage
        + 0.15 * area_coverage
        + 0.23 * (100 - energy_cost_score)
        + 0.05 * (100 - flight_time_score)
        + 0.07 * (100 - hazard_exposure_score)
        - constraint_penalty
```

The component scores are scaled to approximately 0–100. Target coverage is priority-weighted. Area coverage is the percentage of available cells reached by at least one sensor footprint. Energy and time are normalized against budgets. Hazard exposure is the average simulated hazard value along sampled flight segments. No-fly crossings and flight-range violations reduce fitness through penalties. Therefore, there is no guaranteed universal optimum; the result depends on the map, weights, and random search.

## Genetic operators and constraints

- **Selection:** tournament selection samples a configurable number of candidates (four by default) and chooses the one with the highest fitness.
- **Crossover:** segment-swapping exchanges a continuous block of waypoint genes between parent routes.
- **Mutation:** mostly makes small coordinate moves, with occasional larger moves; sensor power and speed may also change.
- **Repair:** clamps coordinates to the grid and relocates waypoints that fall in blocked cells to the nearest free cell.
- **Penalty handling:** if the straight line between waypoints or the return leg crosses a no-fly cell, or a drone exceeds its allowed range including the return trip, its fitness is reduced. This is important because repairing waypoints alone cannot guarantee every connecting segment is safe.

## Assumptions and limitations

This is a **simulation for coursework**, not a flight-certified navigation system. Sensor coverage is represented by a circular radius and does not model line-of-sight, terrain elevation, weather dynamics, or real drone physics. Routes are straight segments between evolved waypoints. The GA penalizes no-fly crossings but does not guarantee a path around every obstacle. The weighted fitness function demonstrates multi-objective trade-offs without implementing a full Pareto-front algorithm.

## Suggestions for a team of three

- **Member 1:** grid model, targets, hazards, chromosome design.
- **Member 2:** fitness function, selection, crossover, mutation, and constraints.
- **Member 3:** visualization, testing, README, and final presentation.

Each member should understand the complete pipeline, but this division makes parallel development easier.
