"""Run the RescueScout UAV disaster-survey optimization simulation."""

from pathlib import Path

from environment import GridEnvironment
from genetic_algorithm import GeneticAlgorithm
from visualization import save_best_plan_plot, save_fitness_plot, save_generation_snapshots


def main():
    project_dir = Path(__file__).resolve().parent
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    environment = GridEnvironment(width=20, height=20, seed=7)
    ga = GeneticAlgorithm(
        environment=environment,
        population_size=70,
        generations=90,
        mutation_rate=0.20,
        crossover_rate=0.90,
        seed=21,
    )

    print("RescueScout UAV mission planner")
    print("Evolving routes, sensor power, and speed settings...\n")
    best = ga.run(patience=25)

    save_fitness_plot(ga.best_history, ga.average_history, output_dir / "fitness_convergence.png")
    save_best_plan_plot(environment, best, output_dir / "best_routes_and_coverage.png")
    save_generation_snapshots(environment, ga.best_by_generation, output_dir / "generation_snapshots.png")

    metrics = best.metrics
    summary_lines = [
        "RESCUESCOUT — BEST MISSION SUMMARY",
        "=" * 38,
        f"Generations completed: {len(ga.best_history) - 1}",
        f"Best fitness: {best.fitness:.2f}",
        f"Priority-weighted target coverage: {metrics['target_coverage_percent']:.1f}%",
        f"Targets detected: {metrics['targets_detected']} / {metrics['total_targets']}",
        f"Map area covered: {metrics['area_coverage_percent']:.1f}%",
        f"Total flight distance: {metrics['distance']:.2f}",
        f"Estimated energy cost: {metrics['energy']:.2f}",
        f"Estimated flight time: {metrics['flight_time']:.2f}",
        f"Average hazard exposure: {metrics['hazard_exposure_percent']:.1f}%",
        f"No-fly segments crossed: {metrics['blocked_segments']}",
        f"Constraint penalty: {metrics['constraint_penalty']:.2f}",
        "",
        "WAYPOINTS (x, y, sensor power, speed)",
        "Sensor power is 0 (off) to 3 (high); speed is 1 (slow) to 3 (fast).",
    ]
    for drone_index, route in enumerate(best.routes, start=1):
        summary_lines.append(f"UAV {drone_index} starts at {environment.starts[drone_index - 1]}:")
        for waypoint_index, point in enumerate(route, start=1):
            summary_lines.append(
                f"  WP {waypoint_index}: ({point.x}, {point.y}), sensor={point.sensor_power}, speed={point.speed}"
            )

    summary_path = output_dir / "run_summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print("Simulation complete. Results saved in the output/ folder.\n")
    print("Best fitness:", f"{best.fitness:.2f}")
    print("Target coverage:", f"{metrics['target_coverage_percent']:.1f}%")
    print("Targets detected:", f"{metrics['targets_detected']} / {metrics['total_targets']}")
    print("Area coverage:", f"{metrics['area_coverage_percent']:.1f}%")
    print("Energy:", f"{metrics['energy']:.2f}")
    print("Flight time:", f"{metrics['flight_time']:.2f}")
    print("Hazard exposure:", f"{metrics['hazard_exposure_percent']:.1f}%")
    print("No-fly segments crossed:", metrics["blocked_segments"])
    print("\nGenerated files:")
    print(" - output/fitness_convergence.png")
    print(" - output/best_routes_and_coverage.png")
    print(" - output/generation_snapshots.png")
    print(" - output/run_summary.txt")


if __name__ == "__main__":
    main()
