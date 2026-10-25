"""Create publication figures and a text summary from the MST benchmark.

Usage:
    python plot_results.py results.csv figures
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results.csv")
OUT_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
COLORS = {2: "#2a78d6", 4: "#1baf7a", 8: "#d67b00", 16: "#b0396d"}
LABELS = {2: r"$E=2V$", 4: r"$E=4V$", 8: r"$E=8V$", 16: r"$E=16V$"}

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


def load_rows() -> list[dict[str, float | int | str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as stream:
        return [
            {
                "algorithm": row["algorithm"],
                "vertices": int(row["vertices"]),
                "edges": int(row["edges"]),
                "factor": int(row["density_factor"]),
                "trial": int(row["trial"]),
                "time": float(row["elapsed_us"]),
                "total": int(row["total_length"]),
            }
            for row in csv.DictReader(stream)
        ]


ROWS = load_rows()
if not ROWS:
    raise SystemExit("benchmark CSV has no observations")


def grouped(algorithm: str) -> dict[tuple[int, int, int], list[float]]:
    values: dict[tuple[int, int, int], list[float]] = defaultdict(list)
    for row in ROWS:
        if row["algorithm"] == algorithm:
            key = (int(row["vertices"]), int(row["edges"]), int(row["factor"]))
            values[key].append(float(row["time"]))
    return values


DATA = {algorithm: grouped(algorithm) for algorithm in ("Kruskal", "Prim")}


def series(algorithm: str, factor: int) -> dict[str, np.ndarray]:
    points = sorted(key for key in DATA[algorithm] if key[2] == factor)
    samples = [np.array(DATA[algorithm][key]) for key in points]
    return {
        "vertices": np.array([key[0] for key in points], dtype=float),
        "edges": np.array([key[1] for key in points], dtype=float),
        "median": np.array([np.median(sample) for sample in samples]),
        "low": np.array([np.min(sample) for sample in samples]),
        "high": np.array([np.max(sample) for sample in samples]),
    }


def all_series(algorithm: str) -> dict[str, np.ndarray]:
    points = sorted(DATA[algorithm])
    samples = [np.array(DATA[algorithm][key]) for key in points]
    return {
        "vertices": np.array([key[0] for key in points], dtype=float),
        "edges": np.array([key[1] for key in points], dtype=float),
        "factor": np.array([key[2] for key in points], dtype=int),
        "median": np.array([np.median(sample) for sample in samples]),
        "low": np.array([np.min(sample) for sample in samples]),
        "high": np.array([np.max(sample) for sample in samples]),
    }


def elog2e(edges: np.ndarray) -> np.ndarray:
    return edges * np.log2(edges)


def thousands(value: float, _position: int = 0) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:g}M"
    if value >= 1_000:
        return f"{value / 1_000:g}k"
    return f"{value:g}"


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT_DIR / f"{name}.pdf")
    fig.savefig(OUT_DIR / f"{name}.png")
    plt.close(fig)


# Figure 1: Kruskal runtime versus E log E, with error bars and fit.
kr = all_series("Kruskal")
x = elog2e(kr["edges"])
y = kr["median"]
fit_c = float(np.dot(x, y) / np.dot(x, x))
fit_y = fit_c * x
r2 = 1.0 - float(np.sum((y - fit_y) ** 2) / np.sum((y - y.mean()) ** 2))

fig, ax = plt.subplots(figsize=(3.5, 2.5))
grid_x = np.linspace(x.min(), x.max(), 400)
ax.plot(grid_x / 1e6, fit_c * grid_x, "--", color=INK_2, linewidth=1.1,
        label=rf"Fit: $cE\log_2E$  ($R^2={r2:.4f}$)")
for factor in (2, 4, 8, 16):
    mask = kr["factor"] == factor
    ax.errorbar(x[mask] / 1e6, y[mask],
                yerr=[y[mask] - kr["low"][mask], kr["high"][mask] - y[mask]],
                fmt="o", color=COLORS[factor], ecolor=COLORS[factor],
                elinewidth=0.7, capsize=2, label=LABELS[factor])
ax.set_xlabel(r"$E\log_2E$ (millions)")
ax.set_ylabel("Runtime (microseconds)")
ax.set_title("Kruskal runtime and $E\\log E$ fit")
ax.legend(frameon=False, loc="upper left", ncol=2)
save(fig, "fig1_runtime_fit")

# Figure 2: normalized Kruskal time across density families.
fig, ax = plt.subplots(figsize=(3.5, 2.5))
for factor in (2, 4, 8, 16):
    data = series("Kruskal", factor)
    ratio = data["median"] / elog2e(data["edges"])
    ax.plot(data["vertices"], ratio, marker="o", color=COLORS[factor],
            label=LABELS[factor])
ax.set_xscale("log")
ax.xaxis.set_major_formatter(FuncFormatter(thousands))
ax.set_xlabel("Buildings $V$ (log scale)")
ax.set_ylabel(r"Time / $(E\log_2E)$")
ax.set_title(r"Kruskal time normalized by $E\log_2E$")
ax.legend(frameon=False, loc="best", ncol=2)
save(fig, "fig2_normalized_time")

# Figure 3: Kruskal against Prim on the same graph families.
fig, ax = plt.subplots(figsize=(3.5, 2.5))
for algorithm, label, color, marker in [
    ("Kruskal", r"Kruskal $O(E\log E)$", "#2a78d6", "o"),
    ("Prim", r"Prim $O(E\log V)$", "#eb6834", "s"),
]:
    data = series(algorithm, 8)
    ax.plot(data["edges"], data["median"], marker=marker, color=color, label=label)
ax.set_xscale("log")
ax.set_yscale("log")
ax.xaxis.set_major_formatter(FuncFormatter(thousands))
ax.set_xlabel("Candidate routes $E$ (log scale; $E=8V$)")
ax.set_ylabel("Runtime (microseconds, log scale)")
ax.set_title("Kruskal versus Prim")
ax.legend(frameon=False, loc="upper left")
save(fig, "fig3_baselines")

# Figure 4: scaling by V for each density, showing both algorithms.
fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.8), sharex=True, sharey=True)
for axis, factor in zip(axes.flat, (2, 4, 8, 16)):
    for algorithm, color, marker in [("Kruskal", "#2a78d6", "o"), ("Prim", "#eb6834", "s")]:
        data = series(algorithm, factor)
        axis.plot(data["vertices"], data["median"], marker=marker, color=color,
                  label=algorithm)
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.xaxis.set_major_formatter(FuncFormatter(thousands))
    axis.set_title(LABELS[factor])
    axis.grid(True, which="both")
axes[0, 0].set_ylabel("Runtime (microseconds)")
axes[1, 0].set_ylabel("Runtime (microseconds)")
axes[1, 0].set_xlabel("Buildings $V$ (log scale)")
axes[1, 1].set_xlabel("Buildings $V$ (log scale)")
axes[0, 1].legend(frameon=False, loc="upper left")
fig.suptitle("Scaling with graph size and route density", y=1.01)
fig.tight_layout()
save(fig, "fig4_density_scaling")


def fmt_table(algorithm: str) -> list[str]:
    lines = [f"{algorithm} median runtime (microseconds):"]
    lines.append(f"{'V':>8}" + "".join(f"{'E=' + str(f) + 'V':>14}" for f in (2, 4, 8, 16)))
    vertices = sorted({key[0] for key in DATA[algorithm]})
    for vertex in vertices:
        row = f"{vertex:>8,}"
        for factor in (2, 4, 8, 16):
            data = series(algorithm, factor)
            index = list(data["vertices"]).index(float(vertex))
            row += f"{data['median'][index]:>14.2f}"
        lines.append(row)
    return lines


summary: list[str] = [
    "# Kruskal and Prim Runtime Experiment",
    "",
    f"Fit for Kruskal: time_us = {fit_c:.6e} * E log2(E), R^2 = {r2:.5f}",
    "",
]
summary.extend(fmt_table("Kruskal"))
summary.append("")
summary.extend(fmt_table("Prim"))
summary.append("")
summary.append("Median Prim/Kruskal ratio at E=8V:")
for vertex in sorted({key[0] for key in DATA["Kruskal"]}):
    kr8 = series("Kruskal", 8)
    pr8 = series("Prim", 8)
    index = list(kr8["vertices"]).index(float(vertex))
    summary.append(f"{vertex:>8,}: {pr8['median'][index] / kr8['median'][index]:.3f}")
summary.append("")
summary.append("Doubling ratios for Kruskal at each density:")
for factor in (2, 4, 8, 16):
    data = series("Kruskal", factor)
    ratios = data["median"][1:] / data["median"][:-1]
    summary.append(f"E={factor}V: " + ", ".join(f"{ratio:.2f}" for ratio in ratios))
(OUT_DIR / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")

print("\n".join(summary))
