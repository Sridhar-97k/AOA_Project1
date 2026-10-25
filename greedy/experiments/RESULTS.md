# Kruskal and Prim Runtime Experiment

The benchmark was run on 2026-10-24 in the project workspace on Windows. The
implementation and benchmark were compiled with MinGW GCC 6.3.0 using
`-std=c++17 -O2 -Wall -Wextra -pedantic`. Processor and memory details were not
available in the recorded run and should be added if the experiment is rerun
for submission.

The benchmark generated 28 connected synthetic graph families with
`V = 100, 200, 400, 800, 1600, 3200, 6400` and `E = 2V, 4V, 8V, 16V`.
Route generation was excluded from timing. Each family used a fixed seed and
seven trials. Both Kruskal and an independent binary-heap Prim implementation
were timed on the same graph, producing 392 rows in `results.csv`.

The plotting script writes four PDF and PNG figures and `summary.txt`:

- `fig1_runtime_fit`: Kruskal runtime with an `E log2(E)` fit and trial ranges.
- `fig2_normalized_time`: Kruskal time divided by `E log2(E)` across densities.
- `fig3_baselines`: Kruskal versus Prim at `E = 8V` on a log-log scale.
- `fig4_density_scaling`: both algorithms across graph sizes and route densities.

The Kruskal fit through the origin is
`time_us = 1.121884e-02 * E log2(E)` with `R^2 = 0.98804` across the 28
median points. The smallest Kruskal case (`V=100`, `E=200`) has a median of
`10.00 microseconds`. The largest case (`V=6400`, `E=102400`) has a median of
`18391.33 microseconds` for Kruskal and `14680.33 microseconds` for Prim.
At `E=8V`, the median Prim/Kruskal ratio ranges from 1.024 to 1.235 across
the tested sizes.

The measurements are consistent with the derived `O(E log E)` upper bound.
They validate the implementation's observed growth but do not prove the
asymptotic bound or model real construction time.
