"""Render original model figures for the offline reader."""

from pathlib import Path
from math import sqrt
from statistics import NormalDist

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ASSETS = Path(__file__).resolve().parents[1] / "assets"
COLORS = ("#91d7ee", "#f4c986", "#afdfb5")
plt.rcParams.update({
    "figure.facecolor": "#19212b", "axes.facecolor": "#19212b",
    "text.color": "#e6edf4", "axes.labelcolor": "#e6edf4",
    "axes.edgecolor": "#637890", "grid.color": "#344356",
    "xtick.color": "#b5c1cd", "ytick.color": "#b5c1cd",
    "font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
})


def axes():
    figure, axis = plt.subplots(figsize=(7.2, 4.1), layout="constrained")
    axis.grid()
    axis.set_axisbelow(True)
    return figure, axis


def mos_current():
    figure, axis = axes()
    drains = [point / 100 for point in range(101)]
    for overdrive, color in zip((0.3, 0.6, 0.9), COLORS):
        channel = [min(drain, overdrive) for drain in drains]
        current = [200 * (overdrive * voltage - voltage**2 / 2) for voltage in channel]
        axis.plot(drains, current, color=color, linewidth=2.3, label=f"{overdrive:g} V overdrive")
        axis.scatter([overdrive], [100 * overdrive**2], color=color, zorder=3)
    axis.set(xlabel="Drain–source voltage (V)", ylabel="Drain current (µA)", xlim=(0, 1))
    axis.legend(frameon=False, loc="upper left")
    figure.savefig(ASSETS / "mos-current.png", dpi=157)
    plt.close(figure)


def clock_skew():
    figure, axis = axes()
    changes = list(range(-85, 46))
    axis.axvspan(-60, 0, color=COLORS[2], alpha=0.17, label="Both checks pass")
    axis.axhline(0, color="#d0dbe5", linewidth=1.0)
    axis.plot(changes, [60 + change for change in changes],
              color=COLORS[0], linewidth=2.3, label="Setup slack")
    axis.plot(changes, [-change for change in changes],
              color=COLORS[1], linewidth=2.3, label="Hold slack")
    axis.scatter([-60, 0], [0, 0], color=[COLORS[0], COLORS[1]], zorder=3)
    axis.set(xlabel="Change in capture clock latency (ps)", ylabel="Slack (ps)",
             xlim=(-85, 45), ylim=(-50, 110))
    axis.legend(frameon=False, loc="upper center", ncol=2)
    figure.savefig(ASSETS / "clock-skew.png", dpi=157)
    plt.close(figure)


def aoi22_order():
    figure, axis = plt.subplots(figsize=(7.2, 3), layout="constrained")
    axis.axis("off")
    axis.set(xlim=(-1.3, 4.3), ylim=(-.7, 2.35))
    rows = (
        (1.45, "PMOS", COLORS[1], ("P", "$V_{DD}$", "P", "Y", "P")),
        (0, "NMOS", COLORS[0], ("Y", "$X_{ab}$", "GND", "$X_{cd}$", "Y")),
    )
    for y, kind, color, nodes in rows:
        axis.hlines(y, 0, 4, color=color, linewidth=7, alpha=.55)
        axis.scatter(range(5), [y] * 5, s=54, color=color)
        axis.text(-.31, y, kind, ha="right", va="center", fontweight="bold")
        for x, node in enumerate(nodes):
            axis.text(x, y - .32, node, ha="center", va="center", fontsize=15)
    for x, gate in zip((.5, 1.5, 2.5, 3.5), "abdc"):
        axis.vlines(x, -.12, 1.87, color="#d8dde5", linewidth=1.7, alpha=.68)
        axis.text(x, 2.02, gate, ha="center", va="center", fontsize=16)
    figure.savefig(ASSETS / "aoi22-order.png", dpi=157)
    plt.close(figure)


def latch_window():
    figure, axis = plt.subplots(figsize=(7.2, 3.2), layout="constrained")
    axis.set(xlim=(470, 730), ylim=(-.1, 2.4), yticks=[], xlabel="Time (ps)",
             xticks=(500, 620, 660, 700))
    axis.spines["left"].set_visible(False)
    axis.axvspan(500, 700, color=COLORS[0], alpha=.10)
    axis.axvspan(660, 700, color=COLORS[1], alpha=.22)
    axis.step([470, 500, 700, 730], [1.48, 1.81, 1.48, 1.48],
              where="post", color=COLORS[0], linewidth=2.4)
    axis.step([470, 620, 730], [.30, .59, .59], where="post",
              color=COLORS[2], linewidth=2.4)
    axis.text(512, 1.97, "Latch transparent", color=COLORS[0], fontsize=15)
    axis.text(615, .07, "Data arrives", ha="right", color=COLORS[2], fontsize=13)
    axis.text(681, 1.11, "Setup\nwindow", ha="center", va="center",
              color=COLORS[1], fontsize=13)
    axis.annotate("", xy=(660, .85), xytext=(620, .85),
                  arrowprops={"arrowstyle": "<->", "color": "#e6edf4"})
    axis.text(640, 1.07, "40 ps\nmargin", ha="center", va="center", fontsize=12)
    figure.savefig(ASSETS / "latch-window.png", dpi=157)
    plt.close(figure)


def multicycle_edges():
    figure, axis = plt.subplots(figsize=(7.2, 3.75), layout="constrained")
    axis.set(xlim=(-.23, 2.35), ylim=(-.35, 3.1), yticks=[], xlabel="Capture time relative to launch",
             xticks=(0, 1, 2), xticklabels=("0", "$T$", "$2T$"))
    axis.spines["left"].set_visible(False)
    rows = (
        (2.18, "Default", 1, 0),
        (1.22, "Setup ×2", 2, 1),
        (.26, "Setup ×2 and hold ×1", 2, 0),
    )
    for y, label, setup_edge, hold_edge in rows:
        axis.hlines(y, 0, 2.12, color="#637890", linewidth=1.3)
        axis.scatter((0, 1, 2), [y] * 3, color="#637890", s=24)
        axis.text(-.12, y + .32, label, ha="left", fontsize=14)
        axis.scatter(setup_edge, y, color=COLORS[0], s=62)
        axis.text(setup_edge, y + .13, "Setup", ha="center", color=COLORS[0], fontsize=12)
        axis.scatter(hold_edge, y, marker="s", color=COLORS[1], s=57)
        axis.text(hold_edge, y - .25, "Hold", ha="center", color=COLORS[1], fontsize=12)
    figure.savefig(ASSETS / "multicycle-edges.png", dpi=157)
    plt.close(figure)


def path_variation():
    figure, axis = axes()
    delays = range(830, 1171)
    for spread, color, label in (
        (sqrt(50), COLORS[0], "Independent gates"),
        (50, COLORS[1], "Perfect positive correlation"),
    ):
        model = NormalDist(1000, spread)
        axis.plot(delays, [model.pdf(delay) for delay in delays],
                  label=label, color=color, linewidth=2.3)
        upper = 1000 + 3 * spread
        axis.axvline(upper, linestyle="--", linewidth=1.25, color=color)
        axis.text(upper + 3, .011 if spread < 10 else .017, f"{upper:g}",
                  color=color, rotation=90, va="bottom")
    axis.set(xlabel="Total delay (lecture time units)", ylabel="Probability density",
             xlim=(830, 1170), ylim=(0, .065))
    axis.legend(frameon=False, loc="upper left")
    figure.savefig(ASSETS / "path-variation.png", dpi=157)
    plt.close(figure)


if __name__ == "__main__":
    mos_current()
    clock_skew()
    aoi22_order()
    latch_window()
    multicycle_edges()
    path_variation()
