#!/usr/bin/env python
"""Every published z, held against the number of draws its own null was built from.

WHY THIS EXISTS. On 2026-08-30 the propagation artefact was given an interval for the first
time, and the interval said something about the artefact rather than about the genes: not one
of its ten largest z values kept a positive interval, and the largest — z = 1825 — had an
interval of [-1753, +5403]. The cause was not the genes. A gene of degree 5 is missed by
almost every draw of a degree-matched null, so the null's spread at that gene is nearly zero,
and any reach at all divides into an enormous z.

That is not a fact about propagation. It is a fact about DIVIDING BY AN ESTIMATED SPREAD, and
this repository does it in nine artefacts. So this tool asks the same question of all of them
at once.

## The three things a large z can mean, only one of which is a finding

  1. A large effect measured against a well-estimated spread. The finding.
  2. A DEGENERATE NULL: the null barely varies, so the denominator is near zero. `knowledge_void`
     publishes 318 occupied lattice cells against a null of 575 with a standard deviation of
     0.95 — under one unit, on a count — and reports z = -270.51. The shortfall is real and
     large; the z is a number about the arithmetic, not about the world.
  3. AN EXTRAPOLATION PAST WHAT THE NULL RESOLVES. A permutation null of N draws cannot
     distinguish any tail probability below 1/(N+1). With the 200 draws used almost everywhere
     here, that floor is 0.005, which under a normal reading is about z = 2.58. Every z above
     it is a distance the experiment measured multiplied out along a curve the experiment
     never sampled.

## What this tool reports, and what it deliberately does not

It reports, per artefact: how many z values are published, the largest, the draw count behind
the null, the resolution floor that count implies, and the z's own standard error — because a
z estimated against N draws inherits the sampling error of the standard deviation in its
denominator, whose relative standard error is 1/sqrt(2N). At 200 draws that is 5%, so a
published z of 1825 carries a standard error of 91 in its own right, before anything about the
data is considered.

It does NOT declare the underlying results wrong. `knowledge_void`'s shortfall is one of the
strongest measurements in this repository. What it says is narrower and, this project having
already published one z that its own interval could not support, worth saying in a tool rather
than a paragraph: **when a null is tight, the z is the wrong published number, and the effect
on its own scale is the right one.**

    python tools/z_audit.py            # the report
    python tools/z_audit.py --check    # exit 1 when a large z has no effect beside it

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "web" / "src" / "data" / "generated"
DEST = ROOT / "out" / "z_audit.json"

#: Draws behind each artefact's null, read from its own source rather than guessed. An
#: artefact whose draw count cannot be established is reported as unknown rather than assumed:
#: assuming it would be inventing the very quantity this tool exists to check against.
DRAWS = {
    "twin_propagation": 200,
    "signal_energy": 200,
    "gene_constraint": 400,
    "hiv_resistance": 200,
    "obesity_thermogenesis": 200,
    "knowledge_shape": 200,
    "knowledge_void": 200,
    "autism_convergence": 200,
    "tail_calibration": None,
    "figures": None,
    "runs": None,
    "points": None,
}

#: Above this, a z is far enough into the tail that no permutation count used in this
#: repository resolves it, and the artefact must publish the effect on its own scale beside
#: it. 10 is not a statistical constant — it is a deliberately permissive line, chosen so that
#: the check flags the artefacts where the question is unarguable rather than every one where
#: it could be raised.
LOUD = 10.0


def normal_quantile(p: float) -> float:
    """The z whose upper tail is `p`, by bisection on erfc. Stdlib has no ppf and importing
    scipy for one number in an audit tool would be the tail wagging the dog."""
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 0.5 * math.erfc(mid / math.sqrt(2)) > p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def walk(node, path: str, out: list) -> None:
    """Collect every z with whatever null summary sits beside it in the same object."""
    if isinstance(node, dict):
        z = node.get("z", node.get("z_score", node.get("z_vs_null")))
        if isinstance(z, (int, float)):
            out.append({
                "path": path,
                "z": float(z),
                "null_mean": node.get("null_mean"),
                "null_sd": node.get("null_sd"),
                "observed": node.get("observed", node.get("score", node.get("raw"))),
                # An interval beside the z is the thing that makes a large one legible, so
                # whether one is present is part of the audit rather than a detail of it.
                #
                # MATCHED BY SHAPE, NOT BY A LIST OF NAMES. The first version of this line
                # carried six literal key names and reported knowledge_shape as publishing a
                # z of -19 with no interval. It publishes `mean_ci95`, which was not in the
                # list. The instrument invented the defect — the same failure this repository
                # found in its own citation audit, which "discovered" nine articles with no
                # notes when the real number was zero, because a regex could not see a second
                # YAML scalar style. A list of names cannot see a name nobody thought of.
                "has_interval": any(
                    k == "ci95" or k.endswith("_ci95") or k.endswith("_ci")
                    or k in ("interval", "se", "ci")
                    for k in node
                ),
            })
        for k, v in node.items():
            walk(v, f"{path}/{k}", out)
    elif isinstance(node, list):
        for v in node:
            walk(v, path + "[]", out)


def audit_one(stem: str, payload) -> dict:
    found: list = []
    walk(payload, "", found)
    if not found:
        return {}

    n = DRAWS.get(stem)
    floor = 1.0 / (n + 1) if n else None
    resolvable = normal_quantile(floor) if floor else None
    # A z's own standard error. The denominator is a standard deviation estimated from n
    # draws, whose relative standard error is 1/sqrt(2n); the z inherits it proportionally.
    rel_se = 1.0 / math.sqrt(2 * n) if n else None

    biggest = max(found, key=lambda r: abs(r["z"]))
    # A null is called TIGHT when its spread is small next to its own centre. That ratio, and
    # not the z, is what says the denominator is doing the work: knowledge_void's null sits at
    # 575 with a spread of 0.95, a coefficient of variation of 0.0017.
    cv = None
    if isinstance(biggest.get("null_sd"), (int, float)) and biggest.get("null_mean"):
        try:
            cv = abs(biggest["null_sd"] / biggest["null_mean"])
        except ZeroDivisionError:
            cv = None

    loud = [r for r in found if abs(r["z"]) > LOUD]
    return {
        "artefact": stem,
        "z_published": len(found),
        "max_abs_z": round(abs(biggest["z"]), 2),
        "max_at": biggest["path"][:70],
        "draws": n,
        "resolution_floor_p": round(floor, 5) if floor else None,
        "z_the_draws_resolve": round(resolvable, 2) if resolvable else None,
        "se_of_the_largest_z": (round(abs(biggest["z"]) * rel_se, 2) if rel_se else None),
        "null_mean_at_max": biggest.get("null_mean"),
        "null_sd_at_max": biggest.get("null_sd"),
        "null_coefficient_of_variation": round(cv, 5) if cv is not None else None,
        "tight_null": bool(cv is not None and cv < 0.01),
        "above_resolution": (sum(1 for r in found if resolvable and abs(r["z"]) > resolvable)
                             if resolvable else None),
        "louder_than_10": len(loud),
        "louder_than_10_with_an_interval": sum(1 for r in loud if r["has_interval"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when a z above the loud line has no interval beside it")
    args = ap.parse_args()

    rows = []
    for f in sorted(GEN.glob("*.json")):
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        r = audit_one(f.stem, payload)
        if r:
            rows.append(r)
    rows.sort(key=lambda r: -r["max_abs_z"])

    total = sum(r["z_published"] for r in rows)
    loud = sum(r["louder_than_10"] for r in rows)
    covered = sum(r["louder_than_10_with_an_interval"] for r in rows)
    tight = [r["artefact"] for r in rows if r["tight_null"]]

    print(f"z audit — {total} published z values across {len(rows)} artefacts\n")
    print(f"  {'artefact':24s} {'n':>5s} {'max|z|':>8s} {'draws':>6s} {'resolves':>9s} "
          f"{'SE(max)':>8s}  null cv")
    for r in rows:
        print(f"  {r['artefact']:24s} {r['z_published']:5d} {r['max_abs_z']:8.1f} "
              f"{str(r['draws'] or '-'):>6s} {str(r['z_the_draws_resolve'] or '-'):>9s} "
              f"{str(r['se_of_the_largest_z'] or '-'):>8s}  "
              f"{r['null_coefficient_of_variation'] if r['null_coefficient_of_variation'] is not None else '-'}"
              f"{'  <- TIGHT NULL' if r['tight_null'] else ''}")

    print(f"\n  {loud} z values above {LOUD:.0f}; {covered} of them carry an interval.")
    if tight:
        print(f"  tight nulls (spread under 1% of the null's own centre): {', '.join(tight)}")
    print("\n  A permutation null of 200 draws resolves no tail below 1/201. Every z past "
          "\n  about 2.6 is a distance measured against a spread, extended along a curve the "
          "\n  experiment never sampled. That is legitimate as an EFFECT SIZE and not as a "
          "\n  significance claim, and the difference is only visible when the effect is "
          "\n  published on its own scale beside the z.")

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({
        "generated": "tools/z_audit.py",
        "governed_by": "docs/references/standards.md §4",
        "question": "Is every published z supported by the null it was computed against?",
        "loud_line": LOUD,
        "totals": {"z_published": total, "louder_than_10": loud,
                   "louder_than_10_with_an_interval": covered,
                   "artefacts_with_a_tight_null": tight},
        "says": (
            "A z is a distance in units of an estimated spread. Three things make one large, "
            "and only the first is a finding: a large effect; a null whose spread is near "
            "zero, which divides any deviation into an enormous number; or a tail the "
            "permutation count never reached. With 200 draws no tail below 1/201 is "
            "resolved, so any z past about 2.6 is an extrapolation. It remains a fair effect "
            "size and stops being a significance claim, and the only way a reader can tell "
            "the two apart is if the effect is published on its own scale beside it."),
        "artefacts": rows,
    }, indent=2), encoding="utf-8")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")

    if args.check:
        # The exemption list lives in index_check.py and is not repeated here. Two tools
        # holding two lists of "artefacts allowed to publish a z without an interval" is how
        # one of them ends up stale, and the whole point of both is that a list which drifts
        # from the filesystem is a defect.
        sys.path.insert(0, str(ROOT / "tools"))
        from index_check import Z_WITHOUT_INTERVAL  # noqa: PLC0415

        bad = [r for r in rows
               if r["louder_than_10"]
               and not r["louder_than_10_with_an_interval"]
               and r["artefact"] not in Z_WITHOUT_INTERVAL]
        if bad:
            for r in bad:
                print(f"  !! {r['artefact']}: {r['louder_than_10']} z values above {LOUD:.0f}, "
                      f"none with an interval")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
