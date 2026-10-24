# Divide-and-Conquer Majority Vote Verification

Decides whether one candidate received more than half of the ballots, using
only equality tests between ballots (no sorting, no tally table).

## Files

- `MajorityVote.java`: the divide-and-conquer algorithm, plus brute-force
  (O(n^2)) and Boyer–Moore (O(n)) baselines. Every equality test is counted.
- `Benchmark.java`: synthetic election generator, correctness tests and
  timing experiments.
- `plot_results.py`: turns `results.csv` into the report's figures.

## Requirements

- Java 11 or newer (tested with OpenJDK 21)
- Python 3 with `matplotlib` and `numpy`

## Running

```bash
javac MajorityVote.java Benchmark.java

# 1. Correctness: exhaustive tests for n <= 8, 200,000 random elections,
#    and every synthetic scenario, checked against both baselines.
java Benchmark verify

# 2. Timing experiments (takes a few minutes), written to results.csv
java -Xmx3g Benchmark bench results.csv

# 3. Figures (PDF + PNG) in figures/, summary table on the console
python3 plot_results.py results.csv figures
```

## Synthetic elections

Each election has 5 candidates and its ballots are shuffled.

| Scenario | Ballots for candidate 0 | Outcome |
|---|---|---|
| LANDSLIDE | 60% | candidate 0 wins |
| NARROW | floor(n/2) + 1 | candidate 0 wins by one ballot |
| TIE | floor(n/2) | no majority |
| FRAGMENTED | uniform over 5 candidates | no majority |

Sizes run from 1,000 to 10,000,000 ballots, 5 trials per size with different
random seeds. Each timing repeats the run until at least 20 ms have elapsed
and reports the average per run, after a JIT warm-up.
