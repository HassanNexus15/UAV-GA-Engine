"""Plots for fitness convergence, UAV trajectories, and coverage snapshots."""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from environment import GridEnvironment
from uav_models import Chromosome


DRONE_COLORS = ["tab:blue", "tab:green", "tab:purple", "tab:orange"]


def _draw_map_background(ax, env: GridEnvironment, title: str, show_hazards: bool = True):
    if show_hazards:
        image = env.hazard.copy()
        image[env.blocked] = np.nan
        cmap = plt.get_cmap("YlOrRd").copy()
        cmap.set_bad(color="dimgray")
        ax.imshow(image, origin="lower", extent=(-0.5, env.width - 0.5, -0.5, env.height - 0.5), cmap=cmap, vmin=0, vmax=1)
    else:
        image = np.zeros_like(env.hazard, dtype=float)
        image[env.blocked] = np.nan
        cmap = plt.get_cmap("Greys").copy()
        cmap.set_bad(color="dimgray")
        ax.imshow(image, origin="lower", extent=(-0.5, env.width - 0.5, -0.5, env.height - 0.5), cmap=cmap, vmin=0, vmax=1)

    for x, y, priority in env.targets:
        ax.scatter(x, y, marker="*", s=55 + 20 * priority, color="gold", edgecolor="black", linewidth=0.7, zorder=6)
    for drone_index, (x, y) in enumerate(env.starts):
        ax.scatter(x, y, marker="s", s=75, color=DRONE_COLORS[drone_index], edgecolor="white", linewidth=0.8, zorder=7)
        ax.text(x + 0.25, y - 0.65, f"Start {drone_index + 1}", fontsize=7, color=DRONE_COLORS[drone_index], weight="bold")

    ax.set_title(title)
    ax.set_xlim(-0.5, env.width - 0.5)
    ax.set_ylim(-0.5, env.height - 0.5)
    ax.set_xticks(range(0, env.width, 2))
    ax.set_yticks(range(0, env.height, 2))
    ax.set_xlabel("X cell")
    ax.set_ylabel("Y cell")
    ax.grid(alpha=0.12, linewidth=0.5)


def _draw_routes(ax, env: GridEnvironment, chromosome: Chromosome, title: str):
    _draw_map_background(ax, env, title, show_hazards=True)
    for drone_index, route in enumerate(chromosome.routes):
        color = DRONE_COLORS[drone_index % len(DRONE_COLORS)]
        # Show the full mission: launch -> waypoints -> return to launch.
        points = [env.starts[drone_index]] + [(point.x, point.y) for point in route] + [env.starts[drone_index]]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        ax.plot(xs, ys, color=color, linewidth=2.0, marker="o", markersize=4, label=f"UAV {drone_index + 1}", zorder=5)
        for waypoint_index, waypoint in enumerate(route, start=1):
            ax.annotate(str(waypoint_index), (waypoint.x, waypoint.y), xytext=(3, 3), textcoords="offset points", fontsize=7, color="black", zorder=8)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)


def _draw_coverage(ax, env: GridEnvironment, chromosome: Chromosome, title: str):
    coverage = env.coverage_map(chromosome).astype(float)
    coverage[env.blocked] = np.nan
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad(color="dimgray")
    image = ax.imshow(coverage, origin="lower", extent=(-0.5, env.width - 0.5, -0.5, env.height - 0.5), cmap=cmap, vmin=0, vmax=max(1, int(np.nanmax(coverage))))
    for x, y, priority in env.targets:
        ax.scatter(x, y, marker="*", s=50 + 15 * priority, color="gold", edgecolor="black", linewidth=0.6, zorder=6)
    ax.set_title(title)
    ax.set_xlim(-0.5, env.width - 0.5)
    ax.set_ylim(-0.5, env.height - 0.5)
    ax.set_xticks(range(0, env.width, 2))
    ax.set_yticks(range(0, env.height, 2))
    ax.set_xlabel("X cell")
    ax.set_ylabel("Y cell")
    ax.grid(alpha=0.12, linewidth=0.5)
    plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Number of sensor footprints")


def save_fitness_plot(best_history: list[float], average_history: list[float], output_path: Path):
    generations = range(len(best_history))
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(generations, best_history, label="Best fitness", linewidth=2)
    ax.plot(generations, average_history, label="Average fitness", linewidth=1.8)
    ax.set_title("RescueScout: Fitness Convergence")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness (higher is better)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def save_best_plan_plot(env: GridEnvironment, best: Chromosome, output_path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    _draw_routes(axes[0], env, best, f"Best evolved routes (fitness {best.fitness:.2f})")
    _draw_coverage(axes[1], env, best, "Sensor coverage heatmap")
    fig.suptitle("RescueScout — Best UAV Mission Plan", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def save_generation_snapshots(
    env: GridEnvironment,
    best_by_generation: list[Chromosome],
    output_path: Path,
):
    """Compare the best-known plan at the start, middle, and end of evolution."""
    if not best_by_generation:
        return
    indexes = sorted(set([0, len(best_by_generation) // 2, len(best_by_generation) - 1]))
    fig, axes = plt.subplots(len(indexes), 2, figsize=(14, 5.0 * len(indexes)))
    if len(indexes) == 1:
        axes = np.array([axes])

    for row, index in enumerate(indexes):
        candidate = best_by_generation[index]
        _draw_routes(axes[row, 0], env, candidate, f"Generation {index}: routes (fitness {candidate.fitness:.2f})")
        _draw_coverage(axes[row, 1], env, candidate, f"Generation {index}: coverage")
    fig.suptitle("Route and Coverage Changes During Genetic Algorithm Evolution", fontsize=14, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
