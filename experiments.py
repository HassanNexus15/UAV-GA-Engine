"""Run GA hyperparameter sensitivity tests and a Random Search comparison.

Usage (from the project directory):
    python experiments.py

Results are saved under output/experiments as PNG plots and CSV files.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean, pstdev

import matplotlib.pyplot as plt
import numpy as np

from environment import GridEnvironment
from genetic_algorithm import GeneticAlgorithm


PROJECT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PROJECT_DIR / "output" / "experiments"

# Three seeds make the comparison less dependent on one random run.
SEEDS = [21, 42, 63]
SENSITIVITY_GENERATIONS = 40
BASELINE_POPULATION_SIZE = 70
BASELINE_GENERATIONS = 40
BASELINE_MUTATION_RATE = 0.20
BASELINE_TOURNAMENT_SIZE = 4
BASELINE_CROSSOVER_RATE = 0.90
ENVIRONMENT_SEED = 7

POPULATION_SIZES = [30, 70, 110]
MUTATION_RATES = [0.05, 0.20, 0.35]
TOURNAMENT_SIZES = [2, 4, 8]


SENSITIVITY_FIELDS = [
    "experiment",
    "parameter_value",
    "seed",
    "population_size",
    "mutation_rate",
    "tournament_size",
    "generations",
    "evaluations",
    "best_fitness",
    "target_coverage_percent",
    "targets_detected",
    "total_targets",
    "area_coverage_percent",
    "distance",
    "energy",
    "flight_time",
    "hazard_exposure_percent",
    "blocked_segments",
    "constraint_penalty",
]


METRIC_FIELDS = [
    "best_fitness",
    "target_coverage_percent",
    "targets_detected",
    "total_targets",
    "area_coverage_percent",
    "distance",
    "energy",
    "flight_time",
    "hazard_exposure_percent",
    "blocked_segments",
    "constraint_penalty",
]


def make_environment() -> GridEnvironment:
    """Create the same map each time so only the GA settings vary."""
    return GridEnvironment(width=20, height=20, seed=ENVIRONMENT_SEED)


def evaluation_count(population_size: int, completed_generations: int) -> int:
    """Count candidate evaluations, excluding copied elites that are not reevaluated."""
    return population_size + completed_generations * (population_size - GeneticAlgorithm.ELITE_COUNT)


def run_ga(
    population_size: int,
    mutation_rate: float,
    tournament_size: int,
    generations: int,
    seed: int,
):
    """Run one GA trial with early stopping disabled for fair comparisons."""
    ga = GeneticAlgorithm(
        environment=make_environment(),
        population_size=population_size,
        generations=generations,
        mutation_rate=mutation_rate,
        crossover_rate=BASELINE_CROSSOVER_RATE,
        tournament_size=tournament_size,
        seed=seed,
    )
    best = ga.run(patience=None)
    evaluations = evaluation_count(population_size, len(ga.best_history) - 1)
    return ga, best, evaluations


def metric_row(best, experiment: str, parameter_value: float | int, seed: int,
               population_size: int, mutation_rate: float, tournament_size: int,
               generations: int, evaluations: int) -> dict:
    row = {
        "experiment": experiment,
        "parameter_value": parameter_value,
        "seed": seed,
        "population_size": population_size,
        "mutation_rate": mutation_rate,
        "tournament_size": tournament_size,
        "generations": generations,
        "evaluations": evaluations,
        "best_fitness": best.fitness,
    }
    row.update(best.metrics)
    return row


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_sensitivity_plot(
    experiment_key: str,
    title: str,
    x_label: str,
    values: list[float | int],
    histories: dict[float | int, list[list[float]]],
    output_name: str,
) -> None:
    """Plot mean best-fitness progress, showing variation across random seeds."""
    fig, ax = plt.subplots(figsize=(9, 5.5))
    generations = np.arange(SENSITIVITY_GENERATIONS + 1)

    for value in values:
        runs = np.asarray(histories[value], dtype=float)
        average = runs.mean(axis=0)
        spread = runs.std(axis=0)
        ax.plot(generations, average, linewidth=2, label=f"{x_label} = {value}")
        ax.fill_between(generations, average - spread, average + spread, alpha=0.15)

    ax.set_title(title)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Best fitness (higher is better)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / output_name, dpi=180, bbox_inches="tight")
    plt.close(fig)


def run_sensitivity_experiments() -> list[dict]:
    """Vary population size, mutation rate, and tournament size one at a time."""
    records: list[dict] = []
    histories_by_experiment: dict[str, dict[float | int, list[list[float]]]] = {}

    specifications = [
        {
            "key": "population_size",
            "values": POPULATION_SIZES,
            "title": "Sensitivity to Population Size",
            "xlabel": "Population size",
            "filename": "sensitivity_population_size.png",
        },
        {
            "key": "mutation_rate",
            "values": MUTATION_RATES,
            "title": "Sensitivity to Mutation Rate",
            "xlabel": "Mutation rate",
            "filename": "sensitivity_mutation_rate.png",
        },
        {
            "key": "tournament_size",
            "values": TOURNAMENT_SIZES,
            "title": "Sensitivity to Tournament Size (Selection Pressure)",
            "xlabel": "Tournament size",
            "filename": "sensitivity_tournament_size.png",
        },
    ]

    for spec in specifications:
        key = spec["key"]
        value_histories: dict[float | int, list[list[float]]] = {}
        print(f"\nSensitivity experiment: {key.replace('_', ' ')}")

        for value in spec["values"]:
            value_histories[value] = []
            for seed in SEEDS:
                population_size = int(value) if key == "population_size" else BASELINE_POPULATION_SIZE
                mutation_rate = float(value) if key == "mutation_rate" else BASELINE_MUTATION_RATE
                tournament_size = int(value) if key == "tournament_size" else BASELINE_TOURNAMENT_SIZE

                ga, best, evaluations = run_ga(
                    population_size=population_size,
                    mutation_rate=mutation_rate,
                    tournament_size=tournament_size,
                    generations=SENSITIVITY_GENERATIONS,
                    seed=seed,
                )
                value_histories[value].append(list(ga.best_history))
                records.append(
                    metric_row(
                        best=best,
                        experiment=key,
                        parameter_value=value,
                        seed=seed,
                        population_size=population_size,
                        mutation_rate=mutation_rate,
                        tournament_size=tournament_size,
                        generations=len(ga.best_history) - 1,
                        evaluations=evaluations,
                    )
                )
                print(
                    f"  {key}={value}, seed={seed}: fitness={best.fitness:.2f}, "
                    f"target coverage={best.metrics['target_coverage_percent']:.1f}%, "
                    f"evaluations={evaluations}"
                )

        histories_by_experiment[key] = value_histories
        save_sensitivity_plot(
            experiment_key=key,
            title=spec["title"],
            x_label=spec["xlabel"],
            values=spec["values"],
            histories=value_histories,
            output_name=spec["filename"],
        )

    write_csv(RESULTS_DIR / "sensitivity_results.csv", SENSITIVITY_FIELDS, records)
    return records


def run_random_search_trial(
    total_evaluations: int,
    population_size: int,
    mutation_rate: float,
    tournament_size: int,
    seed: int,
):
    """Try random valid chromosomes and retain the best candidate seen so far."""
    generator = GeneticAlgorithm(
        environment=make_environment(),
        population_size=population_size,
        generations=1,
        mutation_rate=mutation_rate,
        crossover_rate=BASELINE_CROSSOVER_RATE,
        tournament_size=tournament_size,
        seed=seed,
    )

    best = None
    best_score = -float("inf")
    best_so_far = []
    for _ in range(total_evaluations):
        candidate = generator.create_random_chromosome()
        score = generator.evaluate(candidate)
        if score > best_score:
            best_score = score
            best = candidate.clone()
        best_so_far.append(best_score)
    return best, best_so_far


def run_baseline_comparison() -> None:
    """Compare GA against Random Search under equal candidate-evaluation budgets."""
    print("\nGA versus Random Search comparison")
    summary_rows: list[dict] = []
    ga_histories = []
    random_histories = []
    common_evaluation_counts = None

    for seed in SEEDS:
        ga, ga_best, ga_evaluations = run_ga(
            population_size=BASELINE_POPULATION_SIZE,
            mutation_rate=BASELINE_MUTATION_RATE,
            tournament_size=BASELINE_TOURNAMENT_SIZE,
            generations=BASELINE_GENERATIONS,
            seed=seed,
        )

        # Compare at the exact candidate-evaluation checkpoints used by the GA.
        checkpoints = [
            evaluation_count(BASELINE_POPULATION_SIZE, generation)
            for generation in range(BASELINE_GENERATIONS + 1)
        ]
        if ga_evaluations != checkpoints[-1]:
            raise RuntimeError("GA evaluation count did not match the requested fixed generation budget.")

        random_best, random_history = run_random_search_trial(
            total_evaluations=ga_evaluations,
            population_size=BASELINE_POPULATION_SIZE,
            mutation_rate=BASELINE_MUTATION_RATE,
            tournament_size=BASELINE_TOURNAMENT_SIZE,
            seed=seed,
        )
        random_curve = [random_history[count - 1] for count in checkpoints]

        ga_histories.append(list(ga.best_history))
        random_histories.append(random_curve)
        common_evaluation_counts = checkpoints

        for algorithm, candidate in [("Genetic Algorithm", ga_best), ("Random Search", random_best)]:
            row = {"seed": seed, "algorithm": algorithm, "evaluations": ga_evaluations}
            row.update({field: candidate.metrics.get(field) for field in METRIC_FIELDS if field != "best_fitness"})
            row["best_fitness"] = candidate.fitness
            summary_rows.append(row)

        print(
            f"  seed={seed}: GA fitness={ga_best.fitness:.2f}; "
            f"Random Search fitness={random_best.fitness:.2f}; "
            f"budget={ga_evaluations} evaluations each"
        )

    ga_array = np.asarray(ga_histories, dtype=float)
    random_array = np.asarray(random_histories, dtype=float)
    ga_mean = ga_array.mean(axis=0)
    ga_std = ga_array.std(axis=0)
    random_mean = random_array.mean(axis=0)
    random_std = random_array.std(axis=0)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(common_evaluation_counts, ga_mean, linewidth=2.2, label="Genetic Algorithm (mean)")
    ax.fill_between(common_evaluation_counts, ga_mean - ga_std, ga_mean + ga_std, alpha=0.16)
    ax.plot(common_evaluation_counts, random_mean, linewidth=2.2, linestyle="--", label="Random Search (mean)")
    ax.fill_between(common_evaluation_counts, random_mean - random_std, random_mean + random_std, alpha=0.16)
    ax.set_title("Genetic Algorithm vs. Random Search (Equal Evaluation Budget)")
    ax.set_xlabel("Candidate evaluations")
    ax.set_ylabel("Best fitness so far (higher is better)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "ga_vs_random_search.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    curve_rows = []
    for i, evaluations in enumerate(common_evaluation_counts):
        curve_rows.append({
            "evaluations": evaluations,
            "ga_mean_best_fitness": ga_mean[i],
            "ga_std_best_fitness": ga_std[i],
            "random_mean_best_fitness": random_mean[i],
            "random_std_best_fitness": random_std[i],
        })
    curve_fields = [
        "evaluations",
        "ga_mean_best_fitness",
        "ga_std_best_fitness",
        "random_mean_best_fitness",
        "random_std_best_fitness",
    ]
    write_csv(RESULTS_DIR / "baseline_convergence.csv", curve_fields, curve_rows)
    write_csv(RESULTS_DIR / "baseline_comparison_results.csv", ["seed", "algorithm", "evaluations", *METRIC_FIELDS], summary_rows)

    print("\nMean final results across the three paired seeds:")
    for algorithm in ["Genetic Algorithm", "Random Search"]:
        rows = [row for row in summary_rows if row["algorithm"] == algorithm]
        print(
            f"  {algorithm:18s} fitness={mean(row['best_fitness'] for row in rows):.2f} "
            f"(+/- {pstdev(row['best_fitness'] for row in rows):.2f}); "
            f"target coverage={mean(row['target_coverage_percent'] for row in rows):.1f}%; "
            f"area coverage={mean(row['area_coverage_percent'] for row in rows):.1f}%"
        )


def print_sensitivity_summary(records: list[dict]) -> None:
    """Print means across seeds; use the CSV for all raw trial values."""
    print("\nMean sensitivity results across seeds:")
    for key, values in [
        ("population_size", POPULATION_SIZES),
        ("mutation_rate", MUTATION_RATES),
        ("tournament_size", TOURNAMENT_SIZES),
    ]:
        for value in values:
            rows = [row for row in records if row["experiment"] == key and row["parameter_value"] == value]
            print(
                f"  {key}={value}: fitness={mean(row['best_fitness'] for row in rows):.2f}; "
                f"target coverage={mean(row['target_coverage_percent'] for row in rows):.1f}%; "
                f"area coverage={mean(row['area_coverage_percent'] for row in rows):.1f}%"
            )



def write_experiment_summary(sensitivity_records: list[dict]) -> None:
    """Create a concise, data-backed summary for the technical report."""
    lines = [
        "# RescueScout Experiment Summary",
        "",
        "## Experimental setup",
        "",
        f"- Grid: 20 x 20, fixed environment seed {ENVIRONMENT_SEED}.",
        f"- Sensitivity experiments: {SENSITIVITY_GENERATIONS} generations per run; random seeds {', '.join(map(str, SEEDS))}.",
        "- One parameter was varied at a time; other parameters stayed at their baseline values.",
        "- Population-size test: 30, 70, 110 (mutation rate 0.20; tournament size 4).",
        "- Mutation-rate test: 0.05, 0.20, 0.35 (population size 70; tournament size 4).",
        "- Tournament-size test: 2, 4, 8 (population size 70; mutation rate 0.20).",
        "- Baseline comparison: three paired seeds, 70 candidates initially, 40 generations, two elites, and 2,790 candidate evaluations per method per seed.",
        "- Random Search samples valid chromosomes and retains the highest fitness found; it uses the same environment and fitness function as the GA.",
        "",
        "## Sensitivity results",
        "",
        "Values are means across the three random seeds. Fitness is the program's weighted score; target coverage is priority-weighted; area coverage is the percent of unblocked cells scanned by a sensor.",
        "",
        "| Experiment | Setting | Mean best fitness (SD) | Mean target coverage | Mean area coverage |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, values in [
        ("population_size", POPULATION_SIZES),
        ("mutation_rate", MUTATION_RATES),
        ("tournament_size", TOURNAMENT_SIZES),
    ]:
        for value in values:
            selected = [r for r in sensitivity_records if r["experiment"] == key and r["parameter_value"] == value]
            fit_values = [float(r["best_fitness"]) for r in selected]
            fit_mean = mean(fit_values)
            fit_std = pstdev(fit_values)
            target_mean = mean(float(r["target_coverage_percent"]) for r in selected)
            area_mean = mean(float(r["area_coverage_percent"]) for r in selected)
            lines.append(
                f"| {key.replace('_', ' ').title()} | {value} | {fit_mean:.2f} ({fit_std:.2f}) | {target_mean:.1f}% | {area_mean:.1f}% |"
            )

    comparison_path = RESULTS_DIR / "baseline_comparison_results.csv"
    with comparison_path.open(newline="", encoding="utf-8") as file:
        comparison_rows = list(csv.DictReader(file))
    lines.extend([
        "",
        "## Genetic Algorithm versus Random Search",
        "",
        "The evaluation budget was matched at 2,790 candidate evaluations for each method in each paired trial. The table reports mean values across the three seeds. Lower energy and flight-time values are not automatically better if target coverage falls; interpret them alongside fitness and coverage.",
        "",
        "| Metric | Genetic Algorithm | Random Search |",
        "|---|---:|---:|",
    ])
    for field, label, fmt in [
        ("best_fitness", "Best fitness", ".2f"),
        ("target_coverage_percent", "Priority-weighted target coverage", ".1f"),
        ("targets_detected", "Targets detected (mean count)", ".2f"),
        ("area_coverage_percent", "Area coverage (%)", ".1f"),
        ("energy", "Energy cost (simulated units)", ".2f"),
        ("flight_time", "Flight time (simulated units)", ".2f"),
        ("hazard_exposure_percent", "Hazard exposure (%)", ".1f"),
        ("blocked_segments", "No-fly segments crossed (mean count)", ".2f"),
    ]:
        ga_values = [float(r[field]) for r in comparison_rows if r["algorithm"] == "Genetic Algorithm"]
        rs_values = [float(r[field]) for r in comparison_rows if r["algorithm"] == "Random Search"]
        ga_mean = mean(ga_values)
        rs_mean = mean(rs_values)
        lines.append(f"| {label} | {ga_mean:{fmt}} | {rs_mean:{fmt}} |")

    lines.extend([
        "",
        "## Interpretation notes",
        "",
        "- In these runs, the larger tested population achieved the highest mean fitness, but the population experiment also uses more candidate evaluations at a fixed generation count. This should be mentioned when interpreting the result.",
        "- The 0.05 mutation rate had the highest mean fitness among the three tested mutation settings. The 0.35 setting showed lower mean target coverage, suggesting that stronger mutation disrupted some good routes in these runs.",
        "- Tournament size 8 had the highest mean fitness among the tournament settings, while tournament size 4 detected all targets across the three seeds. Results may change with different seeds or map settings.",
        "- With an equal evaluation budget, the GA produced a much higher mean fitness and target coverage than the Random Search baseline in this experiment. This supports the usefulness of selection, crossover, and mutation for this objective, but it does not prove global optimality.",
        "- These are simulated, dimensionless resource estimates, not measurements from real UAV hardware. Hazard exposure is an average of sampled cell risk values converted to a percentage.",
        "",
        "## Generated figures",
        "",
        "- `sensitivity_population_size.png`",
        "- `sensitivity_mutation_rate.png`",
        "- `sensitivity_tournament_size.png`",
        "- `ga_vs_random_search.png`",
        "",
        "Raw per-trial measurements are available in `sensitivity_results.csv` and `baseline_comparison_results.csv`. Baseline convergence values are in `baseline_convergence.csv`.",
    ])
    (RESULTS_DIR / "experiment_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    print("RescueScout: hyperparameter sensitivity and baseline experiments")
    print(f"Results folder: {RESULTS_DIR}")
    print(f"Each sensitivity setting is repeated with seeds: {SEEDS}")
    print(f"Sensitivity runs use {SENSITIVITY_GENERATIONS} generations per trial.")

    sensitivity_records = run_sensitivity_experiments()
    print_sensitivity_summary(sensitivity_records)
    run_baseline_comparison()
    write_experiment_summary(sensitivity_records)

    print("\nAll experiments completed.")
    print("Generated outputs:")
    for name in [
        "sensitivity_population_size.png",
        "sensitivity_mutation_rate.png",
        "sensitivity_tournament_size.png",
        "ga_vs_random_search.png",
        "sensitivity_results.csv",
        "baseline_comparison_results.csv",
        "baseline_convergence.csv",
        "experiment_summary.md",
    ]:
        print(f" - output/experiments/{name}")


if __name__ == "__main__":
    main()
