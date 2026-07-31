"""Reproduce every claim episode #4 makes, from scratch.

    python run_all.py

Re-runs the whole lab (about four minutes), then checks each number the article states
against what the fresh run produced. Exits non-zero if any of them has drifted.

The simulation needs numpy and mpmath. Regenerating the figures additionally needs
matplotlib and pillow; run_all.py does not require them.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
REF = json.loads((HERE / "metrics_reference.json").read_text(encoding="utf-8"))

print("running the lab (ensemble, control, rewind sweep) ...\n")
subprocess.run([sys.executable, "run_lab.py"], cwd=HERE, check=True)
NEW = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))

fails = []


def check(name, got, want, tol=0.0):
    ok = got == want if tol == 0 else abs(got - want) <= tol
    print(f"  {'PASS' if ok else 'FAIL'}  {name}\n         got {got!r}, expected {want!r}")
    if not ok:
        fails.append(name)


b, c, r, d = NEW["blur"], NEW["control"], NEW["rewind"], NEW["rewind_demo"]
rb, rr, rd = REF["blur"], REF["rewind"], REF["rewind_demo"]

print("THE COUNTING")
check("12,870 ways to split sixteen balls eight and eight",
      math.comb(16, 8), 12870)

print("\nTHE BLUR")
check("uncertainty doubles every 0.28 time units", round(b["doubling_time"], 2), 0.28, 0.01)
check("one nanometre in, a third of the table out",
      round(b["spread_saturated"], 2), round(rb["spread_saturated"], 2), 0.03)
for k in ("8x4", "16x8", "32x16"):
    check(f"the {k} observer saturates at its own ceiling",
          round(b["entropy_final"][k] / b["entropy_ceiling_ln_cells"][k], 3), 1.0, 0.01)

print("\nTHE CONTROL THAT MUST NOT BLUR")
check("perturbation removed: spread stays exactly zero", c["spread_max"], 0.0)
check("perturbation removed: entropy stays exactly zero", max(c["entropy_max"].values()), 0.0)

print("\nTHE REWIND")
check("float64 rewinds 54 ball-ball collisions",
      r["sweep"][0]["collisions_recovered"], rr["sweep"][0]["collisions_recovered"])
check("about three and a half collisions per extra digit",
      round(r["collisions_per_digit"], 1), round(rr["collisions_per_digit"], 1), 0.2)
check("the digit price is linear (R^2)", round(r["fit_r2"], 3) >= 0.99, True)
check("exact reversal re-racks the triangle",
      d["error_exact"] < 1e-6, True)
check("reversal after rounding to a nanometre does not",
      round(d["error_rounded"], 2), round(rd["error_rounded"], 2), 0.02)

print(f"\n{len(fails)} failure(s)" if fails else "\nall claims reproduced")
sys.exit(1 if fails else 0)
