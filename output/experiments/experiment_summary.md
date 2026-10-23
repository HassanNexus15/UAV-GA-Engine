# RescueScout Experiment Summary

## Experimental setup

- Grid: 20 x 20, fixed environment seed 7.
- Sensitivity experiments: 40 generations per run; random seeds 21, 42, 63.
- One parameter was varied at a time; other parameters stayed at their baseline values.
- Population-size test: 30, 70, 110 (mutation rate 0.20; tournament size 4).
- Mutation-rate test: 0.05, 0.20, 0.35 (population size 70; tournament size 4).
- Tournament-size test: 2, 4, 8 (population size 70; mutation rate 0.20).
- Baseline comparison: three paired seeds, 70 candidates initially, 40 generations, two elites, and 2,790 candidate evaluations per method per seed.
- Random Search samples valid chromosomes and retains the highest fitness found; it uses the same environment and fitness function as the GA.

## Sensitivity results

Values are means across the three random seeds. Fitness is the program's weighted score; target coverage is priority-weighted; area coverage is the percent of unblocked cells scanned by a sensor.

| Experiment | Setting | Mean best fitness (SD) | Mean target coverage | Mean area coverage |
|---|---:|---:|---:|---:|
| Population Size | 30 | 68.70 (1.89) | 100.0% | 66.8% |
| Population Size | 70 | 68.79 (1.59) | 100.0% | 54.4% |
| Population Size | 110 | 71.86 (0.23) | 100.0% | 46.9% |
| Mutation Rate | 0.05 | 70.82 (1.26) | 100.0% | 58.6% |
| Mutation Rate | 0.2 | 68.79 (1.59) | 100.0% | 54.4% |
| Mutation Rate | 0.35 | 65.14 (2.65) | 93.3% | 52.0% |
| Tournament Size | 2 | 67.14 (3.12) | 96.7% | 50.7% |
| Tournament Size | 4 | 68.79 (1.59) | 100.0% | 54.4% |
| Tournament Size | 8 | 69.46 (0.69) | 96.7% | 58.9% |

## Genetic Algorithm versus Random Search

The evaluation budget was matched at 2,790 candidate evaluations for each method in each paired trial. The table reports mean values across the three seeds. Lower energy and flight-time values are not automatically better if target coverage falls; interpret them alongside fitness and coverage.

| Metric | Genetic Algorithm | Random Search |
|---|---:|---:|
| Best fitness | 68.79 | 29.66 |
| Priority-weighted target coverage | 100.0 | 58.3 |
| Targets detected (mean count) | 8.00 | 4.67 |
| Area coverage (%) | 54.4 | 40.0 |
| Energy cost (simulated units) | 199.83 | 213.98 |
| Flight time (simulated units) | 59.86 | 62.33 |
| Hazard exposure (%) | 34.1 | 31.8 |
| No-fly segments crossed (mean count) | 0.00 | 1.00 |

## Interpretation notes

- In these runs, the larger tested population achieved the highest mean fitness, but the population experiment also uses more candidate evaluations at a fixed generation count. This should be mentioned when interpreting the result.
- The 0.05 mutation rate had the highest mean fitness among the three tested mutation settings. The 0.35 setting showed lower mean target coverage, suggesting that stronger mutation disrupted some good routes in these runs.
- Tournament size 8 had the highest mean fitness among the tournament settings, while tournament size 4 detected all targets across the three seeds. Results may change with different seeds or map settings.
- With an equal evaluation budget, the GA produced a much higher mean fitness and target coverage than the Random Search baseline in this experiment. This supports the usefulness of selection, crossover, and mutation for this objective, but it does not prove global optimality.
- These are simulated, dimensionless resource estimates, not measurements from real UAV hardware. Hazard exposure is an average of sampled cell risk values converted to a percentage.

## Generated figures

- `sensitivity_population_size.png`
- `sensitivity_mutation_rate.png`
- `sensitivity_tournament_size.png`
- `ga_vs_random_search.png`

Raw per-trial measurements are available in `sensitivity_results.csv` and `baseline_comparison_results.csv`. Baseline convergence values are in `baseline_convergence.csv`.
