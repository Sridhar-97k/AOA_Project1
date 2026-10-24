"""
plot_results.py

Reads results.csv (written by `java Benchmark bench results.csv`) and
produces the experimental figures for the report, as PDF (for LaTeX)
and PNG (for previewing), plus a summary table printed to the console.

Usage:
    python3 plot_results.py [results.csv] [output_dir]
"""
import csv
import math
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "results.csv"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "figures"
os.makedirs(OUT_DIR, exist_ok=True)

# Colors: categorical slots in fixed order, recessive ink for axes and text.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

SCENARIOS = ["LANDSLIDE", "NARROW", "TIE", "FRAGMENTED"]
SCENARIO_LABEL = {
    "LANDSLIDE": "Landslide (60%)",
    "NARROW": "Narrow majority",
    "TIE": "Tie (no majority)",
    "FRAGMENTED": "Fragmented (no majority)",
}
SCENARIO_STYLE = {
    "LANDSLIDE": (BLUE, "o"),
    "NARROW": (ORANGE, "s"),
    "TIE": (AQUA, "^"),
    "FRAGMENTED": (YELLOW, "D"),
}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.edgecolor": INK_2,
    "axes.labelcolor": INK,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 1.4,
    "lines.markersize": 4,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
FIGSIZE = (3.5, 2.5)  # one IEEE column


# ----------------------------------------------------------------------
# Load data: (algorithm, scenario) -> n -> list of (time_ms, comparisons)
# ----------------------------------------------------------------------
data = defaultdict(lambda: defaultdict(list))
with open(CSV_PATH) as f:
    for row in csv.DictReader(f):
        key = (row["algorithm"], row["scenario"])
        data[key][int(row["n"])].append((float(row["time_ms"]), int(row["comparisons"])))


def series(algorithm, scenario):
    """Sorted n, median time, min time, max time, median comparisons."""
    by_n = data[(algorithm, scenario)]
    ns = np.array(sorted(by_n))
    t = [np.array([x[0] for x in by_n[n]]) for n in ns]
    c = [np.array([x[1] for x in by_n[n]]) for n in ns]
    return (ns, np.array([np.median(v) for v in t]),
            np.array([v.min() for v in t]), np.array([v.max() for v in t]),
            np.array([np.median(v) for v in c]))


def nlogn(n):
    return n * np.log2(n)


def comparison_bound(n):
    return np.array([2 * k * math.ceil(math.log2(k)) + (k - 1) for k in n], dtype=float)


def thousands(x, _pos=None):
    if x >= 1e6:
        return f"{x / 1e6:g}M"
    if x >= 1e3:
        return f"{x / 1e3:g}k"
    return f"{x:g}"


def save(fig, name):
    fig.savefig(os.path.join(OUT_DIR, name + ".pdf"))
    fig.savefig(os.path.join(OUT_DIR, name + ".png"))
    plt.close(fig)


# ----------------------------------------------------------------------
# Fig. 1: D&C running time vs. fitted c * n log2 n (worst case: TIE)
# ----------------------------------------------------------------------
ns, med, lo, hi, _ = series("DivideAndConquer", "TIE")
x = nlogn(ns)
c_fit = float(np.dot(x, med) / np.dot(x, x))          # least squares through origin
pred = c_fit * x
r2 = 1 - np.sum((med - pred) ** 2) / np.sum((med - med.mean()) ** 2)

fig, ax = plt.subplots(figsize=FIGSIZE)
grid_n = np.linspace(ns.min(), ns.max(), 400)
ax.plot(grid_n / 1e6, c_fit * nlogn(grid_n), "--", color=INK_2, linewidth=1.1,
        label=rf"Fit: $c\,n\log_2 n$  ($R^2={r2:.4f}$)")
ax.errorbar(ns / 1e6, med, yerr=[med - lo, hi - med], fmt="o", color=BLUE,
            ecolor=BLUE, elinewidth=0.8, capsize=2,
            label="Measured (median of 5 trials)")
ax.set_xlabel("Number of ballots $n$ (millions)")
ax.set_ylabel("Running time (ms)")
ax.set_title("Divide-and-conquer running time (tie elections)")
ax.legend(frameon=False, loc="upper left")
save(fig, "fig1_runtime_fit")
fit_summary = (c_fit, r2)

# ----------------------------------------------------------------------
# Fig. 2: running time normalized by n log2 n, all scenarios
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=FIGSIZE)
for s in SCENARIOS:
    ns, med, _, _, _ = series("DivideAndConquer", s)
    color, marker = SCENARIO_STYLE[s]
    ax.plot(ns, med * 1e6 / nlogn(ns), marker=marker, color=color,
            label=SCENARIO_LABEL[s])
ax.set_xscale("log")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(thousands))
ax.set_ylim(bottom=0)
ax.set_xlabel("Number of ballots $n$ (log scale)")
ax.set_ylabel(r"Time / $(n \log_2 n)$  (ns)")
ax.set_title(r"Running time normalized by $n\log_2 n$")
ax.legend(frameon=False, loc="lower right", ncol=1)
save(fig, "fig2_normalized_time")

# ----------------------------------------------------------------------
# Fig. 3: equality tests normalized by n log2 n, with the proven bound
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=FIGSIZE)
ns_all = None
for s in SCENARIOS:
    ns, _, _, _, comps = series("DivideAndConquer", s)
    ns_all = ns
    color, marker = SCENARIO_STYLE[s]
    ax.plot(ns, comps / nlogn(ns), marker=marker, color=color, label=SCENARIO_LABEL[s])
ax.plot(ns_all, comparison_bound(ns_all) / nlogn(ns_all), "--", color=INK_2,
        linewidth=1.1, label=r"Bound $2n\lceil\log_2 n\rceil + n - 1$")
ax.set_xscale("log")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(thousands))
ax.set_ylim(0, None)
ax.set_xlabel("Number of ballots $n$ (log scale)")
ax.set_ylabel(r"Equality tests / $(n \log_2 n)$")
ax.set_title("Ballot comparisons per $n\\log_2 n$")
ax.legend(frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.55))
save(fig, "fig3_comparisons")

# ----------------------------------------------------------------------
# Fig. 4: D&C vs. brute force vs. Boyer-Moore (tie elections, log-log)
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=FIGSIZE)
for alg, label, color, marker in [
    ("BruteForce", r"Brute force $O(n^2)$", AQUA, "^"),
    ("DivideAndConquer", r"Divide and conquer $O(n\log n)$", BLUE, "o"),
    ("BoyerMoore", r"Boyer–Moore $O(n)$", ORANGE, "s"),
]:
    ns, med, _, _, _ = series(alg, "TIE")
    ax.plot(ns, med, marker=marker, color=color, label=label)
ax.set_xscale("log")
ax.set_yscale("log")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(thousands))
ax.set_xlabel("Number of ballots $n$ (log scale)")
ax.set_ylabel("Running time (ms, log scale)")
ax.set_title("Comparison with baseline methods (tie elections)")
ax.legend(frameon=False, loc="lower right")
save(fig, "fig4_baselines")

# ----------------------------------------------------------------------
# Console summary (for the report's results table)
# ----------------------------------------------------------------------
print(f"Fig. 1 fit: time_ms = {fit_summary[0]:.4e} * n log2 n,  R^2 = {fit_summary[1]:.5f}\n")
print("Divide and conquer, median running time (ms):")
header = f"{'n':>12}" + "".join(f"{s:>13}" for s in SCENARIOS)
print(header)
for i, n in enumerate(series("DivideAndConquer", "TIE")[0]):
    row = f"{n:>12,}"
    for s in SCENARIOS:
        row += f"{series('DivideAndConquer', s)[1][i]:>13.3f}"
    print(row)

print("\nEquality tests (median) vs. proven bound, tie elections:")
ns, _, _, _, comps = series("DivideAndConquer", "TIE")
for n, c, b in zip(ns, comps, comparison_bound(ns)):
    print(f"{n:>12,}  tests={int(c):>14,}  bound={int(b):>14,}  ratio={c / b:.3f}")

print("\nDoubling ratios T(2n)/T(n) for tie elections (n log n predicts slightly above 2):")
for i in range(len(ns) - 1):
    if ns[i + 1] == 2 * ns[i]:
        med = series("DivideAndConquer", "TIE")[1]
        pred = nlogn(ns[i + 1]) / nlogn(ns[i])
        print(f"  {ns[i]:>10,} -> {ns[i + 1]:>10,}: measured {med[i + 1] / med[i]:.2f}, predicted {pred:.2f}")
