"""Render two original model figures for the offline reader."""

from pathlib import Path

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


if __name__ == "__main__":
    mos_current()
    clock_skew()
