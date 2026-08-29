"""The measurement space itself, as a set of lines rather than as a table.

WHAT THIS IS FOR. Every other artefact here answers a question about ONE gene. This one is
for a question about the space they live in: do the genes a rule caught run differently
through the measurements than everything else, or does the rule just relabel the middle?

That question has no scatter plot. Two axes show a pair; a matrix of scatters shows every
pair and hides the individual that is extreme in one measurement and ordinary in four —
which is precisely the shape of every finding this site publishes. Parallel coordinates
(Inselberg, 1985) is the form that takes it: one vertical axis per measurement, and each gene
a polyline crossing all of them. A rule firing becomes a visible CROSSING rather than a
lookup.

## Why this ships a sample and not all 18,140

Eighteen thousand polylines is eighteen thousand SVG nodes, and a browser asked to lay those
out is a browser that stops answering.

BOTH LAYERS ARE SAMPLED, and the first version got this wrong in a way worth recording. It
kept every flagged gene and thinned only the rest — which produced a plot where the flagged
WERE the corpus, and the background stopped being something to judge "different from the
rest" against. Now each rule contributes at most a fixed number of lines so no single one
floods the ink, and the ground is an evenly-thinned sample of the unflagged. Both rates are
reported, because a sample a reader mistakes for a census is worse than no plot.

## The axes, and why they are ranks

The variables span six orders of magnitude (papers), a bounded ratio (VUS share), a signed
effect (dependency) and a count. On their own linear scales the papers axis is one line at
the bottom and seventeen thousand crammed at the top. Every axis is therefore drawn on its
own RANK, which makes them uniform by construction — and the interface says so, because a
rank axis a reader mistakes for a value axis inverts every relationship they read off it.

Run after the other gene tools:  `python tools/gene_space.py`
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DEST = ROOT / "web" / "public" / "data" / "gene" / "space.json"

# SVG lays out one node per line, so the budget is the browser's and not the argument's.
# ~3,000 total is fluid; 6,000 is not.
GROUND = 1500          # faint lines standing for the corpus
PER_RULE = 260         # bright lines per rule, so no single rule floods the plot


def load(name: str) -> dict:
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"genes": {}}


def main() -> int:
    index = load("gene_index.json")
    world = load("gene_world.json")
    ds = load("gene_datasheet.json")
    ins = load("gene_insights.json")
    att = load("gene_attention.json")

    if not index["genes"]:
        print("out/gene_index.json absent — run tools/gene_index.py first")
        return 1

    rows: list[dict] = []
    for sym in index["genes"]:
        w = world["genes"].get(sym, {})
        sheet = ds["genes"].get(sym, {})
        con = w.get("con") or {}
        clin = w.get("clin") or {}
        dep = sheet.get("dep") or {}
        exp = sheet.get("exp") or {}
        a = att["genes"].get(sym, {})

        values = {
            "papers": a.get("papers"),
            # Inverted so that "up" means "more constrained" on every axis: an axis where up
            # sometimes means more and sometimes less is a plot that cannot be read.
            "constraint": -con["loeuf"] if con.get("loeuf") is not None else None,
            "dependency": (dep["dependent"] / dep["n"]) if dep.get("n") else None,
            "breadth": exp.get("types"),
            "unread": clin.get("vusShare") if clin.get("total", 0) >= 20 else None,
        }
        # A gene with fewer than three of the five measured is a line that is mostly gaps;
        # it carries no shape and only adds ink.
        if sum(1 for v in values.values() if v is not None) < 3:
            continue

        rows.append({
            "id": sym,
            "v": {k: (round(v, 4) if isinstance(v, float) else v)
                  for k, v in values.items() if v is not None},
            **({"c": ins["genes"][sym]} if sym in ins.get("genes", {}) else {}),
        })

    flagged_all = [r for r in rows if r.get("c")]
    plain = [r for r in rows if not r.get("c")]

    # BOTH LAYERS ARE THINNED, and that is the correction rather than the compromise. Keeping
    # every flagged gene and a handful of others made a plot in which the flagged WERE the
    # corpus — the background stopped being a comparison and the eye had nothing to judge
    # "different from the rest" against. Each rule is capped so no single one floods the ink,
    # and the ground is sampled to stand for the whole.
    seen: set[str] = set()
    flagged: list[dict] = []
    per_rule_counts: dict[str, int] = {}
    for rule in sorted({c for r in flagged_all for c in r["c"]}):
        members = [r for r in flagged_all if rule in r["c"] and r["id"] not in seen]
        step_r = max(1, len(members) // PER_RULE)
        kept = members[::step_r][:PER_RULE]
        per_rule_counts[rule] = len(kept)
        for r in kept:
            seen.add(r["id"])
            flagged.append(r)

    step = max(1, len(plain) // GROUND) if plain else 1
    kept_plain = plain[::step]
    sample = flagged + kept_plain

    payload = {
        "generated": "tools/gene_space.py",
        "premise": (
            "Do the genes a rule caught run differently through the measurements than "
            "everything else, or does the rule relabel the middle? Two axes show a pair; a "
            "matrix of scatters hides the gene that is extreme in one measurement and "
            "ordinary in four, which is the shape of every finding here."
        ),
        "sampling": (
            f"Both layers are sampled, and neither is the corpus. Each rule contributes at "
            f"most {PER_RULE} lines so no single one floods the ink "
            f"({len(flagged):,} of {len(flagged_all):,} flagged genes); the ground is every "
            f"{step}th unflagged gene ({len(kept_plain):,} of {len(plain):,}). Keeping every "
            "flagged gene made a plot in which the flagged were the corpus, and the "
            "background stopped being something to judge difference against."
        ),
        "axes": ["papers", "constraint", "dependency", "breadth", "unread"],
        "scope": {
            "eligible": len(rows),
            "flagged": len(flagged),
            "flaggedTotal": len(flagged_all),
            "perRule": per_rule_counts,
            "ground": len(kept_plain),
            "thinnedEvery": step,
            "total": len(index["genes"]),
        },
        "rows": sample,
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"{len(sample):,} lines shipped ({DEST.stat().st_size / 1024:,.0f} kB)")
    print(f"  flagged sampled      {len(flagged):>6,} of {len(flagged_all):,}")
    print(f"  ground thinned 1/{step:<3}  {len(kept_plain):>6,} of {len(plain):,}")
    print(f"  eligible of corpus   {len(rows):>6,} of {len(index['genes']):,}")
    print(f"wrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
