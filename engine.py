"""Event-driven hard-disk billiard.

Collision times are solved analytically and the state is advanced exactly to each
contact, so the integrator is time-reversible up to the arithmetic it runs on.
That property is the whole point of this lab: it lets us separate what the physics
loses (nothing) from what the observer loses (everything).

Two implementations of the same dynamics:
  - vectorised over an ensemble of universes, float64      -> the blur experiment
  - one universe, any numeric type (float or mpmath.mpf)   -> the rewind experiment
"""

import numpy as np

W, H, R = 1.0, 0.5, 0.015
N = 16

PAIR_I, PAIR_J = np.triu_indices(N, 1)
NPAIR = len(PAIR_I)


def rack(num=float):
    """15 balls racked on the right, cue ball on the left, aimed slightly off centre.

    Every literal is an exact decimal so the same initial condition can be built at
    any working precision without an irrational creeping in.
    """
    sp = num("0.031")          # centre-to-centre spacing inside the rack
    pitch = num("0.0268")      # column pitch (~ sp * sqrt(3)/2, rounded to a decimal)
    mid = num("0.2467")        # deliberately off any round fraction of the table, so
    x = num("0.7513")          # no ball starts life sitting on a coarse-graining line

    pos = [[num("0.2030"), mid]]
    for col in range(5):
        n = col + 1
        y = mid - sp * num(str(n - 1)) / num("2")
        for _ in range(n):
            pos.append([x, y])
            y = y + sp
        x = x + pitch

    vel = [[num("0"), num("0")] for _ in range(N)]
    vel[0] = [num("0.90"), num("0.013")]
    return pos, vel


# --------------------------------------------------------------------------- ensemble

def rack_ensemble(m, sigma, seed=20260728):
    """m copies of the same table; copy 0 is exact, the rest are jittered by sigma."""
    p, v = rack()
    pos = np.tile(np.asarray(p, float), (m, 1, 1))
    vel = np.tile(np.asarray(v, float), (m, 1, 1))
    if sigma > 0:
        rng = np.random.default_rng(seed)
        pos[1:] += rng.normal(0.0, sigma, (m - 1, N, 2))
    return pos, vel


def _next_event(pos, vel):
    m = pos.shape[0]
    hi = np.array([W - R, H - R])

    with np.errstate(divide="ignore", invalid="ignore"):
        t_hi = (hi - pos) / vel
        t_lo = (R - pos) / vel
    tw = np.where(vel > 0, t_hi, np.where(vel < 0, t_lo, np.inf))
    tw = np.where(tw > 0, tw, np.inf).reshape(m, 2 * N)

    dr = pos[:, PAIR_J] - pos[:, PAIR_I]
    dv = vel[:, PAIR_J] - vel[:, PAIR_I]
    b = np.einsum("mpk,mpk->mp", dr, dv)
    a = np.einsum("mpk,mpk->mp", dv, dv)
    c = np.einsum("mpk,mpk->mp", dr, dr) - (2 * R) ** 2
    disc = b * b - a * c
    ok = (b < 0) & (disc > 0) & (a > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        tp = (-b - np.sqrt(np.where(ok, disc, 0.0))) / np.where(ok, a, 1.0)
    tp = np.where(ok & (tp > 0), tp, np.inf)

    cand = np.concatenate([tw, tp], axis=1)
    k = np.argmin(cand, axis=1)
    return cand[np.arange(m), k], k


def _collide(pos, vel, k, hit):
    u = np.nonzero(hit)[0]
    kk = k[u]

    wall = kk < 2 * N
    uw, kw = u[wall], kk[wall]
    vel[uw, kw // 2, kw % 2] *= -1

    up, kp = u[~wall], kk[~wall] - 2 * N
    if up.size:
        i, j = PAIR_I[kp], PAIR_J[kp]
        dr = pos[up, j] - pos[up, i]
        n = dr / np.linalg.norm(dr, axis=1, keepdims=True)
        dv = vel[up, j] - vel[up, i]
        s = np.sum(dv * n, axis=1, keepdims=True) * n
        vel[up, i] += s
        vel[up, j] -= s
    return int(wall.sum()), int((~wall).sum())


def advance(pos, vel, dt):
    """Evolve every universe forward by dt. Each keeps its own event schedule."""
    rem = np.full(pos.shape[0], float(dt))
    walls = pairs = 0
    while True:
        t, k = _next_event(pos, vel)
        step = np.minimum(t, rem)
        pos += vel * step[:, None, None]
        rem -= step
        hit = t <= step
        if not hit.any():
            return walls, pairs
        w, p = _collide(pos, vel, k, hit)
        walls += w
        pairs += p


# ------------------------------------------------------------------------- one table

def _next_scalar(pos, vel, sqrt, inf):
    best, kind, idx = inf, None, None
    for i in range(N):
        for ax, lim in ((0, W - R), (1, H - R)):
            v = vel[i][ax]
            if v > 0:
                t = (lim - pos[i][ax]) / v
            elif v < 0:
                t = (R - pos[i][ax]) / v
            else:
                continue
            if 0 < t < best:
                best, kind, idx = t, "wall", (i, ax)

    dd = 4 * R * R
    for a_ in range(N):
        for b_ in range(a_ + 1, N):
            drx = pos[b_][0] - pos[a_][0]
            dry = pos[b_][1] - pos[a_][1]
            dvx = vel[b_][0] - vel[a_][0]
            dvy = vel[b_][1] - vel[a_][1]
            b = drx * dvx + dry * dvy
            if b >= 0:
                continue
            a = dvx * dvx + dvy * dvy
            if a <= 0:
                continue
            c = drx * drx + dry * dry - dd
            disc = b * b - a * c
            if disc <= 0:
                continue
            t = (-b - sqrt(disc)) / a
            if 0 < t < best:
                best, kind, idx = t, "pair", (a_, b_)
    return best, kind, idx


def _apply_scalar(pos, vel, kind, idx, sqrt):
    if kind == "wall":
        i, ax = idx
        vel[i][ax] = -vel[i][ax]
    else:
        i, j = idx
        drx = pos[j][0] - pos[i][0]
        dry = pos[j][1] - pos[i][1]
        d = sqrt(drx * drx + dry * dry)
        nx, ny = drx / d, dry / d
        s = (vel[j][0] - vel[i][0]) * nx + (vel[j][1] - vel[i][1]) * ny
        vel[i][0] += s * nx
        vel[i][1] += s * ny
        vel[j][0] -= s * nx
        vel[j][1] -= s * ny


def run_scalar(pos, vel, T, sqrt, inf=float("inf")):
    """Evolve one table forward by T in place. Returns the ball-ball collision count."""
    rem = T
    pairs = 0
    while True:
        t, kind, idx = _next_scalar(pos, vel, sqrt, inf)
        done = t > rem
        step = rem if done else t
        for p, v in zip(pos, vel):
            p[0] += v[0] * step
            p[1] += v[1] * step
        if done:
            return pairs
        rem -= step
        _apply_scalar(pos, vel, kind, idx, sqrt)
        pairs += kind == "pair"


def reverse(vel):
    for v in vel:
        v[0] = -v[0]
        v[1] = -v[1]


# ---------------------------------------------------------------------- observables

_GRID_OFFSETS = np.random.default_rng(7).random((8, 2))    # fixed once, for every call


def coarse_entropy(pos, nx, ny):
    """Mean over balls of the Shannon entropy of one ball's coarse position, in nats.

    This is the observer's MARGINAL knowledge: where is ball i, to the resolution of
    the grid. It ignores correlations between balls, so it is a floor on the full
    coarse-grained entropy, not the whole of it. Miller-Madow corrected.

    Averaged over eight fixed placements of the grid origin (wrapped), so that a
    cloud much smaller than one cell reads as ~0 bits instead of flickering between
    0 and 1 as it drifts across a cell line: information must never appear to be
    GAINED because of where the ruler happens to lie.
    """
    m = pos.shape[0]
    out = np.zeros(N)
    for ox, oy in _GRID_OFFSETS:
        ix = np.floor(pos[:, :, 0] / W * nx + ox).astype(int) % nx
        iy = np.floor(pos[:, :, 1] / H * ny + oy).astype(int) % ny
        cell = ix * ny + iy
        for b in range(N):
            counts = np.bincount(cell[:, b], minlength=nx * ny)
            p = counts[counts > 0] / m
            out[b] += -(p * np.log(p)).sum() + (len(p) - 1) / (2 * m)
    return float(out.mean() / len(_GRID_OFFSETS))


def spread(pos):
    """RMS distance of the jittered universes from the exact one, over all coordinates."""
    d = pos[1:] - pos[0]
    return float(np.sqrt((d ** 2).mean()))
