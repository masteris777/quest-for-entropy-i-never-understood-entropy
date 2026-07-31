"""Figures for episode #4. Light theme: the Substack page is white."""

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Rectangle

import engine as E

BG = "#faf8f4"
INK = "#1a1a1a"
MUTED = "#8a8580"
RED = "#c1362f"
BLUE = "#2f5fa8"
GREEN = "#2e7d4f"
AMBER = "#c98a1b"

BALL = plt.get_cmap("turbo")(np.linspace(0.08, 0.95, E.N))

D = np.load("frames.npz")
Rw = np.load("rewind_frames.npz")
MET = json.load(open("metrics.json", encoding="utf-8"))

times, frames = D["times"], D["frames"]
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})


def table(ax, pad=0.02, top=0.055):
    ax.add_patch(Rectangle((0, 0), E.W, E.H, fill=False, lw=1.4, ec=INK, zorder=5))
    ax.set_xlim(-pad, E.W + pad)
    ax.set_ylim(-pad, E.H + top)
    ax.set_aspect("equal")
    ax.axis("off")


def cloud(ax, f, size=3.4, alpha=0.10):
    for b in range(E.N):
        ax.scatter(f[:, b, 0], f[:, b, 1], s=size, color=BALL[b],
                   alpha=alpha, linewidths=0, zorder=3)


# ------------------------------------------------------------------ 1. the hero

def hero():
    picks = [0.0, 6.0, 7.6, 24.0]
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 5.8), facecolor=BG)
    for ax, t in zip(axes.ravel(), picks):
        i = int(round(t / (times[1] - times[0])))
        ax.set_facecolor(BG)
        table(ax)
        for lag, al in ((4, 0.019), (2, 0.035), (0, 0.077)):
            j = max(i - lag, 0)
            cloud(ax, frames[j], alpha=al)
        if t == 0.0:
            for b in range(E.N):
                ax.scatter(frames[0][0, b, 0], frames[0][0, b, 1], s=46,
                           color=BALL[b], zorder=6, linewidths=0)
        ax.text(0.012, E.H + 0.012, f"t = {t:g}", color=MUTED, fontsize=11, ha="left")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99, wspace=0.04, hspace=0.06)
    fig.savefig("hero_wax_break.png", dpi=150, facecolor=BG)
    plt.close(fig)
    print("hero_wax_break.png")


# ------------------------------------------------------------------- 2. the blur

def blur_gif():
    idx = range(0, int(round(14.0 / (times[1] - times[0]))) + 1)
    fig, ax = plt.subplots(figsize=(6.4, 3.6), facecolor=BG)
    ax.set_facecolor(BG)
    table(ax)
    pts = [ax.scatter([], [], s=9, color=BALL[b], alpha=0.06, linewidths=0, zorder=3)
           for b in range(E.N)]
    solid = [ax.scatter([], [], s=110, color=BALL[b], zorder=6, linewidths=0,
                        edgecolors="none")
             for b in range(E.N)]
    lab = ax.text(0.012, E.H + 0.012, "", color=INK, fontsize=10, ha="left")
    sub = ax.text(0.988, E.H + 0.012, "", color=MUTED, fontsize=9, ha="right")

    def draw(i):
        f = frames[i]
        for b in range(E.N):
            pts[b].set_offsets(f[:, b])
            solid[b].set_offsets(f[:1, b])
        lab.set_text(f"t = {times[i]:5.1f}")
        sub.set_text(f"uncertainty  {D['spreads'][i]:.1e}")
        return pts + solid + [lab, sub]

    ani = FuncAnimation(fig, draw, frames=idx, blit=True)
    ani.save("blur.gif", writer=PillowWriter(fps=12), dpi=100,
             savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    print("blur.gif")


# --------------------------------------------------------------- 3. the two curves

def two_curves():
    S = D["S_16x8"] / np.log(2)
    ceil = MET["blur"]["entropy_ceiling_ln_cells"]["16x8"] / np.log(2)
    fig, ax = plt.subplots(figsize=(8.4, 4.6), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axhline(ceil, color=MUTED, lw=1, ls=":")
    ax.text(6.6, ceil + 0.16, "the ceiling: everything a 16x8 grid can tell apart - 7 bits",
            color=MUTED, fontsize=9, ha="left")
    ax.plot(times, S, color=RED, lw=2.6)
    ax.plot(times, np.zeros_like(times), color=BLUE, lw=2.6)
    ax.text(13.9, 4.30, "my missing information -\nthe observer's entropy, 16x8 grid",
            color=RED, fontsize=11)
    ax.text(9.2, 0.32, "what the world itself forgets: nothing (Liouville)",
            color=BLUE, fontsize=11)
    ax.text(0.4, -0.62, "control, perturbation removed: 0.000 at every single step",
            color=GREEN, fontsize=10)
    ax.set_xlabel("time on the table")
    ax.set_ylabel("missing information per ball  (bits)")
    ax.set_xlim(0, 24)
    ax.set_ylim(-0.95, ceil + 0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("two_curves.png", dpi=160, facecolor=BG)
    plt.close(fig)
    print("two_curves.png")


# --------------------------------------------------------------- 4. the resolution

def resolution():
    fig, ax = plt.subplots(figsize=(8.4, 4.6), facecolor=BG)
    ax.set_facecolor(BG)
    for (nx, ny), col in zip([(32, 16), (16, 8), (8, 4)], (RED, AMBER, BLUE)):
        k = f"{nx}x{ny}"
        c = int(np.log2(nx * ny))
        ax.axhline(c, color=col, lw=0.9, ls=":", alpha=0.7)
        ax.plot(times, D[f"S_{k}"] / np.log(2), color=col, lw=2.4,
                label=f"{nx*ny} cells - ceiling {c} bits")
    ax.set_xlabel("time on the table")
    ax.set_ylabel("missing information per ball  (bits)")
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 9.9)
    ax.legend(frameon=False, loc="lower right", fontsize=10,
              title="how finely I look", title_fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("resolution.png", dpi=160, facecolor=BG)
    plt.close(fig)
    print("resolution.png")


# ----------------------------------------------------------------- 5. the rewind

def rewind_gif():
    ex, ro = Rw["exact"], Rw["rounded"]
    n = len(ex)
    half = n // 2
    start = ex[0]
    fig, axes = plt.subplots(2, 1, figsize=(6.0, 6.0), facecolor=BG)
    titles = ("full precision", f"rounded to a nanometre at the flip")
    art = []
    for ax, ttl, col in zip(axes, titles, (GREEN, RED)):
        ax.set_facecolor(BG)
        table(ax)
        ax.scatter(start[:, 0], start[:, 1], s=54, facecolor="none",
                   edgecolor=MUTED, lw=0.9, zorder=2)
        sc = [ax.scatter([], [], s=42, color=BALL[b], zorder=6, linewidths=0)
              for b in range(E.N)]
        tx = ax.text(0.012, E.H + 0.012, ttl, color=col, fontsize=11, ha="left")
        art.append((sc, tx, ttl, col))
    clock = axes[0].text(0.988, E.H + 0.012, "", color=MUTED, fontsize=10, ha="right")

    def draw(i):
        out = [clock]
        for data, (sc, tx, ttl, col) in zip((ex, ro), art):
            for b in range(E.N):
                sc[b].set_offsets(data[i, b:b + 1])
            out += sc
        dt = float(Rw["dt"])
        if i < half:
            clock.set_text(f"running forward    t = {i * dt:4.1f}")
        else:
            clock.set_text(f"running backward   t = {float(Rw['t_demo']) - (i - half) * dt:4.1f}")
        return out

    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99, hspace=0.10)
    ani = FuncAnimation(fig, draw, frames=range(0, n), blit=True)
    ani.save("rewind.gif", writer=PillowWriter(fps=14), dpi=100,
             savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    print("rewind.gif")


# -------------------------------------------------------------- 6. the digit price

def precision():
    sw = MET["rewind"]["sweep"]
    d = np.array([s["digits"] for s in sw])
    c = np.array([s["collisions_recovered"] for s in sw], float)
    a, b = MET["rewind"]["collisions_per_digit"], MET["rewind"]["fit_intercept"]

    fig, ax = plt.subplots(figsize=(8.4, 4.6), facecolor=BG)
    ax.set_facecolor(BG)
    xs = np.linspace(12, 132, 20)
    ax.plot(xs, a * xs + b, color=MUTED, lw=1.2, ls="--",
            label=f"{a:.1f} collisions per extra digit")
    ax.plot(d, c, "o-", color=RED, lw=2.2, ms=7)
    ax.annotate("float64\n(what your computer uses)", (d[0], c[0]),
                textcoords="offset points", xytext=(16, -6), color=MUTED, fontsize=9)
    ax.set_xlabel("digits of precision carried")
    ax.set_ylabel("ball-ball collisions that come back")
    ax.set_xlim(10, 134)
    ax.set_ylim(0, 500)
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("precision.png", dpi=160, facecolor=BG)
    plt.close(fig)
    print("precision.png")


if __name__ == "__main__":
    hero()
    two_curves()
    resolution()
    precision()
    blur_gif()
    rewind_gif()
