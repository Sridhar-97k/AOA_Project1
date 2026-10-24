"""Plot Kruskal benchmark data. Requires Pillow: python -m pip install Pillow."""

from __future__ import annotations

import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def load(path: Path) -> list[dict[str, float]]:
    grouped: dict[tuple[int, int, int], list[float]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            key = (int(row["vertices"]), int(row["edges"]), int(row["density_factor"]))
            grouped[key].append(float(row["elapsed_us"]))
    if not grouped:
        raise ValueError("benchmark CSV has no observations")
    return [
        {"vertices": n, "edges": e, "factor": factor, "time": statistics.median(samples)}
        for (n, e, factor), samples in sorted(grouped.items())
    ]


def axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
         xmax: float, ymax: float, xlabel: str, ylabel: str) -> None:
    left, top, right, bottom = box
    grid = "#dce4ec"
    def tick_label(value: float) -> str:
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}k"
        return f"{value:.2g}"
    for tick in range(6):
        y = bottom - (bottom - top) * tick / 5
        x = left + (right - left) * tick / 5
        draw.line((left, y, right, y), fill=grid, width=2)
        draw.line((x, top, x, bottom), fill=grid, width=2)
        draw.text((left - 14, y), tick_label(ymax * tick / 5),
                  font=font(18), fill="#344054", anchor="rm")
        draw.text((x, bottom + 12), tick_label(xmax * tick / 5),
                  font=font(18), fill="#344054", anchor="mt")
    draw.line((left, top, left, bottom, right, bottom), fill="#263445", width=3)
    draw.text(((left + right) / 2, bottom + 66), xlabel,
              font=font(21), fill="#263445", anchor="mm")
    draw.text((left, top - 30), ylabel, font=font(19, True), fill="#263445", anchor="ls")


def point(value: float, maximum: float, low: int, high: int) -> float:
    return low + (high - low) * value / maximum


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python plot_results.py BENCHMARK.csv OUTPUT.png")
    observations = load(Path(sys.argv[1]))
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (1700, 860), "white")
    draw = ImageDraw.Draw(image)
    draw.text((850, 50), "Kruskal MST runtime", font=font(34, True),
              fill="#16243a", anchor="mm")
    draw.text((850, 93), "Median of 7 trials; graph generation excluded from timing",
              font=font(21), fill="#536275", anchor="mm")

    left_box = (120, 175, 790, 635)
    right_box = (980, 175, 1620, 635)
    xvalues = [row["edges"] * math.log2(row["edges"]) for row in observations]
    yvalues = [row["time"] for row in observations]
    ratios = [y / x for x, y in zip(xvalues, yvalues)]
    xmax = max(xvalues) * 1.08
    ymax = max(yvalues) * 1.12
    emax = max(row["edges"] for row in observations) * 1.08
    rmax = max(ratios) * 1.2
    axes(draw, left_box, xmax, ymax, "E log2(E)", "Time per run (microseconds)")
    axes(draw, right_box, emax, rmax, "Number of candidate routes E", "Time / (E log2 E)")

    scale = sum(x * y for x, y in zip(xvalues, yvalues)) / sum(x * x for x in xvalues)
    draw.line((left_box[0], left_box[3],
               point(max(xvalues), xmax, left_box[0], left_box[2]),
               point(scale * max(xvalues), ymax, left_box[3], left_box[1])),
              fill="#67768a", width=4)
    colors = {2: "#1769aa", 4: "#00876c", 8: "#d67b00", 16: "#b0396d"}
    for row, x, y, ratio in zip(observations, xvalues, yvalues, ratios):
        color = colors[int(row["factor"])]
        px = point(x, xmax, left_box[0], left_box[2])
        py = point(y, ymax, left_box[3], left_box[1])
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=color)
        rx = point(row["edges"], emax, right_box[0], right_box[2])
        ry = point(ratio, rmax, right_box[3], right_box[1])
        draw.ellipse((rx - 5, ry - 5, rx + 5, ry + 5), fill=color)

    draw.line((120, 785, 170, 785), fill="#67768a", width=4)
    draw.text((185, 785), "fitted E log2(E) trend", font=font(18),
              fill="#344054", anchor="lm")
    for index, (factor, color) in enumerate(colors.items()):
        x = 640 + index * 225
        draw.ellipse((x, 778, x + 15, 793), fill=color)
        draw.text((x + 25, 785), f"E = {factor}V", font=font(17),
                  fill="#344054", anchor="lm")
    image.save(output, optimize=True)
    print(f"Wrote {output} from {len(observations)} graph sizes")


if __name__ == "__main__":
    main()
