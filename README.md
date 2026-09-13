# I Never Understood Entropy — companion repository

**Article:** [Quest for Entropy #4 — "I Never Understood Entropy"](https://questforentropy.substack.com/p/i-never-understood-entropy)

**Series:** ← [#3 The Machine Takes a Quantum Exam](https://github.com/masteris777/quest-for-entropy-quantum-exam) · [#5 Building a Wave](https://github.com/masteris777/quest-for-entropy-building-a-wave) →

Evidence repo for **Quest for Entropy #4: [“I Never Understood Entropy”](article.md)** — a
sixteen-ball elastic billiard, and what it says about the difference between what a system
keeps and what an observer can hold.

## Run it

```
python run_all.py
```

About four minutes. It re-runs the whole lab from scratch and then checks every number the
article states against the fresh output, printing PASS or FAIL for each and exiting non-zero
if any has drifted. Only `numpy` and `mpmath` are needed; `matplotlib` and `pillow` are extra
and only for regenerating the figures.

Compare with `expected_output/run_all.txt`, captured from a real run.

## What is in here

```
run_all.py                the reproduction check - the point of the repo
engine.py                 the billiard: exact collision times, reversible up to arithmetic
run_lab.py                the three experiments (blur, control, rewind sweep)
make_figures.py           every figure in the article, from the lab's own output
metrics_reference.json    the certified run this article was written against
metrics.json              written fresh by run_all.py, compared against the reference
figures/                  the article's figures as published
article.md, assets/       the article as published
```

## The three experiments

**The blur.** Four thousand copies of the same table, differing by one nanometre in the
starting positions. Measures how fast the observer's picture spreads (a doubling time), and the
coarse-grained entropy of that picture on three different grids.

**The control.** The identical ensemble with the nanometre removed. If the blur were an artefact
of the arithmetic rather than of the physics, this would blur too. It does not: spread is exactly
0.0 at every step.

**The rewind.** One table, run forward, every velocity flipped, run back. In exact arithmetic the
break shot un-breaks. We sweep the working precision from 16 to 128 digits and count how many
ball-ball collisions come back before the triangle stops reassembling. The answer is linear in
digits — about three and a half collisions per digit.

## Scope

The entropy measured here is the **per-ball marginal**: where is each ball, to the resolution of
the grid, averaged over balls. It ignores the information carried in the correlations between
balls, so it is a **floor** on the full coarse-grained entropy, not the whole of it. It is
Miller-Madow corrected and estimated from four thousand samples per point.

The estimate is additionally **averaged over eight fixed placements of the grid origin**. Without
this, a cloud much smaller than one cell flickers between "all in one cell" (0 bits) and
"straddling a cell line" (~1 bit) as it drifts past grid lines — an artefact of where the ruler
lies, which would read as information being gained. Averaging the ruler's placement removes it.

The fine-grained entropy is not measured at all. It is constant by Liouville's theorem, and the
runnable demonstration that nothing is truly lost is the rewind, not a plotted line.

## What this does NOT claim

> This is a **toy and a teaching machine, not a result.** Sixteen balls on a rectangle are not a
> gas, not a universe, and not evidence about either. Nothing here is new physics; it is a
> century-old picture, rebuilt small enough to watch it move. It does not claim entropy is
> "subjective" — the counting version needs no observer at all. It does not explain why the
> universe began in a low-entropy state, and it does not touch quantum mechanics anywhere.

## How this was made

The author is a software architect, not a physicist. The direction, the questions and the calls
are his; the heavy lifting — the math, the physics checks, the code, the sums — is AI. Every
experiment declares its pass marks before it runs, results are challenged by independent
adversarial AI review, and every mistake caught goes into a public honesty ledger. Every number
is printed by code in this repository.

## License

Code: MIT. Article text and figures: CC BY 4.0. See `LICENSE`.
