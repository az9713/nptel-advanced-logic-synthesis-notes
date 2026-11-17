"""Deterministic numerical checks for the execution slice and its timing model."""

import argparse
from itertools import product
from math import isclose, log, sqrt
from statistics import NormalDist


def mos():
    beta, overdrive = 200.0, 0.6  # microamperes per volt squared, volts

    def current(drain):
        effective = min(drain, overdrive)
        return beta * (overdrive * effective - effective**2 / 2)

    assert isclose(current(0), 0)
    assert isclose(current(0.2), 20)
    assert isclose(current(overdrive), 36)
    assert isclose(current(1.0), current(overdrive))
    print("MOS current: 20 uA at 0.2 V, 36 uA in ideal saturation")


def cmos():
    for a, b, c in product((False, True), repeat=3):
        pull_down = (a and b) or c
        pull_up = (not a or not b) and not c
        assert pull_up != pull_down
    tau = 2 * 20  # kilohms times femtofarads gives picoseconds
    crossing, slew = tau * log(2), tau * log(9)
    assert isclose(crossing, 27.7258872224)
    assert isclose(slew, 87.8889830934)
    print(f"RC: 50% crossing {crossing:.2f} ps, 90%-10% slew {slew:.2f} ps")


def sizing():
    effort = sqrt((4 / 3) * 2 * 12)
    last_input = 12 / effort
    first_effort = (4 / 3) * 2 * last_input
    assert isclose(first_effort, effort)
    delay = 2 * effort + 3
    assert isclose(delay, 14.313708499)
    assert 3 * (64 ** (1 / 3) + 1) < 5 * (64 ** (1 / 5) + 1)
    assert isclose(1 / (1 + 0.5), 2 / 3)
    print(f"Logical effort: stage effort {effort:.3f}, normalized delay {delay:.3f}")


def library():
    def delay(slew_ps, load_ff):
        slew_position = (slew_ps - 10) / 40
        load_position = (load_ff - 5) / 10
        near = 20 + load_position * (35 - 20)
        far = 30 + load_position * (55 - 30)
        return near + slew_position * (far - near)

    assert [delay(s, c) for s, c in product((10, 50), (5, 15))] == [20, 35, 30, 55]
    assert isclose(delay(20, 11), 33)
    for a, b, c in product((0, 1), repeat=3):
        assert ((a & b) | (a & c)) == (a & (b | c))
    print("Liberty example: bilinear delay 33 ps; factoring holds for all bit inputs")


def constraints():
    budget = 1000 - 180 - 220 - 50
    assert budget == 550
    assert budget - 70 == 480
    for endpoints, expected in [((-80, -25, 12), (-80, -105, 2)),
                                ((-60, -10, -10), (-60, -80, 3))]:
        negatives = [value for value in endpoints if value < 0]
        assert (min(endpoints), sum(negatives), len(negatives)) == expected
    print("Constraints: initial internal budget 550 ps, then 480 ps")


def datapath():
    for a, b, c in product(range(16), repeat=3):
        parity = a ^ b ^ c
        majority = (a & b) | (a & c) | (b & c)
        assert parity + (majority << 1) == a + b + c
    clock_switching = 40e-15 * 0.8**2 * 1e9
    assert isclose(0.25 * clock_switching, 6.4e-6)
    print("Datapath: 4,096 carry-save identities; gated branch uses 6.4 uW")


def closure():
    old_setup, old_hold = 26, -18
    max_increase, min_increase = 35, 22
    assert (old_setup - max_increase, old_hold + min_increase) == (-9, 4)
    parent_slack = 680 - (300 + 450)
    standalone_slack = 680 - (100 + 450)
    assert (parent_slack, standalone_slack) == (-70, 130)
    print("Closure: buffer setup/hold -9/+4 ps; block parent slack -70 ps")


def sta():
    incoming = {"a": [("start", 15, 25)], "b": [("start", 9, 30)],
                "end": [("a", 12, 38), ("b", 22, 32)]}
    earliest, latest = {"start": 0}, {"start": 0}
    for node, arcs in incoming.items():
        earliest[node] = min(earliest[prev] + early for prev, early, _ in arcs)
        latest[node] = max(latest[prev] + late for prev, _, late in arcs)
    assert (earliest["end"], latest["end"]) == (27, 63)
    setup = (1000 + 95 - 60 - 25) - (60 + 80 + 810)
    hold = (60 + 35 + 30) - (95 + 20 + 10)
    assert (setup, hold) == (60, 0)
    downstream = 1.0 * (10 + 20 + 30)
    assert (downstream + 0.5 * 20, downstream + 1.0 * 30) == (70, 90)
    print("STA: path setup/hold +60/0 ps; RC leaf moments 70 and 90 ps")


def variation():
    slack = (1000 + 0.95 * 80 - 50) - 1.05 * (80 + 900)
    assert isclose(slack, -3)
    assert isclose(slack + (1.05 - 0.95) * 80, 5)
    assert isclose(0.8 * 12 / (36 + 12), 0.20)
    spreads = [sqrt(6**2 + 8**2 + 2 * rho * 6 * 8) for rho in (0, 0.5, 1)]
    assert spreads == [10, sqrt(148), 14]
    assert isclose(NormalDist().cdf(3)**2, 0.9973020262)
    print("Variation: derated slack -3 ps, ideal coupled step 0.20 V")


def equivalence():
    def next_result(reset, enable, state, value):
        return 0 if reset else value if enable else state

    for a, b, reset, enable in product((0, 1), repeat=4):
        for x, y, z in product((0, 1, 17, 127, 250, 255), repeat=3):
            select = a & b
            shared = (x + (y if select else z)) % 256
            duplicated = (x + y) % 256 if select else (x + z) % 256
            for state in (0, 26, 255):
                assert next_result(reset, enable, state, shared) == next_result(
                    reset, enable, state, duplicated
                )
    assert (9 + 4, 9 + 7) == (13, 16)
    assert next_result(1, 0, 26, 13) == 0
    print("Equivalence: bounded input grid passed; reversed select yields 13 vs 16")


LABS = (mos, cmos, sizing, library, constraints, datapath, closure, sta, variation, equivalence)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", choices=("all", *(item.__name__ for item in LABS)),
                        default="all", nargs="?")
    selected = parser.parse_args().lab
    for item in LABS:
        if selected in ("all", item.__name__):
            item()
