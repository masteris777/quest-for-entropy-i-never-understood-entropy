"""The break-shot lab: what the table keeps and what the observer loses.

Three experiments on one 16-ball elastic billiard.

  A. THE BLUR      an ensemble of tables differing by one nanometre; measure how fast
                   the observer's picture spreads, and the coarse-grained entropy of
                   that picture at three different resolutions.
  A'. THE CONTROL  the identical ensemble with the nanometre removed. If the blur were
                   an artefact of the arithmetic this would blur too. It must not.
  B. THE REWIND    one table, run forward, every velocity flipped, run back. Exact
                   arithmetic re-racks it. Rounded arithmetic does not. Sweep the
                   precision and measure what a digit buys.

Writes metrics.json (every number the article may quote), frames.npz (the blur
animation) and rewind_frames.npz (the two-panel rewind animation).
"""

import json
import math
import time

import numpy as np
from mpmath import mp, mpf

import engine as E

OUT = {}

M = 4000
SIGMA = 1e-9
T_END = 24.0
DT = 0.2
GRIDS = [(8, 4), (16, 8), (32, 16)]
KEEP = 1200                     # universes kept for the animation


def blur(sigma, label, keep_frames=False):
    pos, vel = E.rack_ensemble(M, sigma)
    times, spreads = [0.0], [E.spread(pos)]
    ents = {f"{nx}x{ny}": [E.coarse_entropy(pos, nx, ny)] for nx, ny in GRIDS}
    frames = [pos[:KEEP].astype(np.float32).copy()] if keep_frames else None
    pairs = 0

    t = 0.0
    t0 = time.time()
    while t < T_END - 1e-12:
        _, p = E.advance(pos, vel, DT)
        pairs += p
        t += DT
        times.append(t)
        spreads.append(E.spread(pos))
        for nx, ny in GRIDS:
            ents[f"{nx}x{ny}"].append(E.coarse_entropy(pos, nx, ny))
        if keep_frames:
            frames.append(pos[:KEEP].astype(np.float32).copy())
    print(f"  {label}: {time.time() - t0:.1f}s, {pairs / M:.0f} ball-ball collisions per table")
    return np.array(times), np.array(spreads), ents, frames


print("A. the blur")
times, spreads, ents, frames = blur(SIGMA, "perturbed", keep_frames=True)

lo, hi = 1e-8, 1e-2                      # the clean exponential window
w = (spreads > lo) & (spreads < hi)
slope, intercept = np.polyfit(times[w], np.log(spreads[w]), 1)
lam = float(slope)

sat = float(np.mean(spreads[times >= T_END - 4.0]))
fill = float(times[np.argmax(spreads > 0.5 * sat)])

OUT["blur"] = {
    "universes": M,
    "perturbation": SIGMA,
    "t_end": T_END,
    "dt": DT,
    "lyapunov_per_time": lam,
    "lyapunov_fit_window": [float(times[w][0]), float(times[w][-1])],
    "lyapunov_fit_points": int(w.sum()),
    "doubling_time": float(math.log(2) / lam),
    "spread_initial": float(spreads[0]),
    "spread_saturated": sat,
    "t_half_saturation": fill,
    "entropy_final": {k: float(v[-1]) for k, v in ents.items()},
    "entropy_ceiling_ln_cells": {f"{nx}x{ny}": float(np.log(nx * ny)) for nx, ny in GRIDS},
}

print("A'. the control (perturbation removed)")
c_times, c_spreads, c_ents, _ = blur(0.0, "control")
OUT["control"] = {
    "perturbation": 0.0,
    "spread_max": float(np.max(c_spreads)),
    "entropy_max": {k: float(np.max(v)) for k, v in c_ents.items()},
    "bit_identical_throughout": bool(np.max(c_spreads) == 0.0),
}

np.savez_compressed(
    "frames.npz",
    times=times, spreads=spreads, control_spreads=c_spreads,
    frames=np.array(frames),
    **{f"S_{k}": np.array(v) for k, v in ents.items()},
    **{f"C_{k}": np.array(v) for k, v in c_ents.items()},
)

# ------------------------------------------------------------------ B. the rewind

TOL = 1e-6


def round_trip(T, dps=None):
    """Forward T, flip every velocity, forward T. Returns the worst position error."""
    if dps is None:
        num, sqrt, T_ = float, math.sqrt, float(T)
    else:
        mp.dps = dps
        num, sqrt, T_ = (lambda s: mpf(s)), mp.sqrt, mpf(str(T))
    pos, vel = E.rack(num)
    ref = [row[:] for row in pos]
    n = E.run_scalar(pos, vel, T_, sqrt)
    E.reverse(vel)
    E.run_scalar(pos, vel, T_, sqrt)
    err = max(abs(a[k] - b[k]) for a, b in zip(pos, ref) for k in (0, 1))
    return float(err), n


def horizon(dps):
    """Largest T (to 0.25) whose round trip still lands within TOL."""
    T = 1.0
    while T < 400:
        e, _ = round_trip(2 * T, dps)
        if e > TOL:
            break
        T *= 2
    good, bad = T, min(2 * T, 400.0)
    while bad - good > 0.25:
        mid = (good + bad) / 2
        e, _ = round_trip(mid, dps)
        if e <= TOL:
            good = mid
        else:
            bad = mid
    _, n = round_trip(good, dps)
    return good, n


print("B. the rewind")
sweep = []
for dps in [None, 20, 24, 32, 48, 64, 96, 128]:
    t0 = time.time()
    T, n = horizon(dps)
    digits = 15.95 if dps is None else float(dps)
    sweep.append({"dps": dps or "float64", "digits": digits,
                  "t_recovered": T, "collisions_recovered": n})
    print(f"  {str(dps or 'float64'):>8}  T={T:6.2f}  {n:4d} ball-ball collisions"
          f"  ({time.time() - t0:.1f}s)")

d = np.array([s["digits"] for s in sweep])
c = np.array([s["collisions_recovered"] for s in sweep], float)
a, b = np.polyfit(d, c, 1)

OUT["rewind"] = {
    "tolerance": TOL,
    "sweep": sweep,
    "collisions_per_digit": float(a),
    "fit_intercept": float(b),
    "fit_r2": float(1 - ((c - (a * d + b)) ** 2).sum() / ((c - c.mean()) ** 2).sum()),
    "lyapunov_per_collision": float(math.log(10) / a),
}

# the two-panel demonstration: same run, reversed exactly vs reversed after rounding
T_DEMO = 8.0
ROUND_TO = 9                    # decimals; on a one-metre table that is a nanometre


def trace(pos, vel, T, dt):
    out = []
    steps = int(round(T / dt))
    for _ in range(steps):
        out.append([[p[0], p[1]] for p in pos])
        E.run_scalar(pos, vel, dt, math.sqrt)
    out.append([[p[0], p[1]] for p in pos])
    return out


demo = {}
for name, rounding in (("exact", None), ("rounded", ROUND_TO)):
    pos, vel = E.rack()
    fwd = trace(pos, vel, T_DEMO, DT)
    if rounding is not None:
        for p, v in zip(pos, vel):
            for k in (0, 1):
                p[k] = round(p[k], rounding)
                v[k] = round(v[k], rounding)
    E.reverse(vel)
    back = trace(pos, vel, T_DEMO, DT)
    ref, _ = E.rack()
    err = max(abs(a[k] - b[k]) for a, b in zip(pos, ref) for k in (0, 1))
    demo[name] = {"final_error": err, "frames": np.array(fwd + back, dtype=np.float32)}
    print(f"  demo {name:>8}: position error after the round trip {err:.3e}")

OUT["rewind_demo"] = {
    "t": T_DEMO,
    "rounded_to_decimals": ROUND_TO,
    "error_exact": demo["exact"]["final_error"],
    "error_rounded": demo["rounded"]["final_error"],
    "ball_radius": E.R,
}

np.savez_compressed("rewind_frames.npz",
                    exact=demo["exact"]["frames"], rounded=demo["rounded"]["frames"],
                    dt=DT, t_demo=T_DEMO)

OUT["table"] = {"balls": E.N, "radius": E.R, "width": E.W, "height": E.H,
                "walls": "elastic", "friction": 0.0}

with open("metrics.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(OUT, f, indent=2)
print("\nwrote metrics.json, frames.npz, rewind_frames.npz")
