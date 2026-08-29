"""What the layers say when you read two of them at once.

THE GAP THIS FILLS. The navigator shows seven layers side by side and never says a word about
what they mean together. But almost everything a person actually wants to know about a gene
lives in a DISAGREEMENT between two measurements, not inside either one:

  * A gene under strong selection in human populations that cells do not need is a gene whose
    importance is organismal — development, immunity, a tissue no dish contains. The cell
    assay is not merely silent about it; it is the wrong instrument, and a pipeline that ranks
    on the assay will discard it every time.
  * A gene every cell line needs that human populations tolerate breaking is the opposite
    warning: either the culture is the artefact, or the constraint estimate is.
  * A constrained gene whose variants nobody can classify is not an interesting mystery. It is
    a gene the field has already decided matters and has not funded the assay for, and that
    intersection is a priority list nobody publishes.
  * Pathogenic variants inside annotated domains while the uncertain ones fall outside is
    weak evidence that the uncertain ones are tolerated — the single most useful thing a
    positional map can say to a curator.

Each observation below is a RULE WITH A STATED THRESHOLD, applied to every gene, and reported
with how many genes it caught. Not a score, not a ranking, not a composite: a reader who
disagrees with a cut can see it and move it, which is the difference between an argument and
an oracle.

## The honest limit, said once and inherited by all of them

Every input carries attention bias. Constraint is measured where people sequenced; dependency
where somebody cultured a line; variants where a clinic sent a sample; domains where a curator
wrote an annotation. An intersection of two biased measurements is not less biased than
either — it is differently biased, and no rule here can tell a real disagreement from two
different sampling frames. They are prompts to look, never conclusions.

Run after the other gene tools:  `python tools/gene_insights.py`
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DEST = OUT / "gene_insights.json"

# Every cut, in one place, so the rules below read as prose and the numbers are auditable.
T = {
    # gnomAD's constrained decile, their own recommendation for prioritising.
    "loeufConstrained": 0.35,
    # Above 1.0 a gene shows about as much loss of function as chance predicts.
    "loeufTolerant": 1.0,
    # DepMap's own cut for "this line depends on this gene".
    "dependent": -0.5,
    # A gene needed by nearly every line is a poison rather than a target.
    "panShare": 0.90,
    # Needed by some and not most: the shape a selective target has.
    "selectiveLo": 0.02,
    "selectiveHi": 0.50,
    # Below this many submitted variants a share is noise.
    "minVariants": 20,
    "vusHigh": 0.70,
    # A gene expressed above this in most cell types is not tissue-restricted.
    "broadShare": 0.60,
}


def load(name: str) -> dict:
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"genes": {}}


def main() -> int:
    index = load("gene_index.json")
    world = load("gene_world.json")
    geo = load("gene_geometry.json")
    dom = load("gene_domains.json")
    ds = load("gene_datasheet.json")

    if not index["genes"]:
        print("out/gene_index.json absent — run tools/gene_index.py first")
        return 1

    per: dict[str, list[str]] = {}
    counts: Counter = Counter()
    eligible: Counter = Counter()

    for sym in index["genes"]:
        w = world["genes"].get(sym, {})
        g = geo["genes"].get(sym, {})
        d = dom["genes"].get(sym, {})
        sheet = (ds["genes"].get(sym) or {})
        con = w.get("con") or {}
        clin = w.get("clin") or {}
        dep = sheet.get("dep") or {}
        exp = sheet.get("exp") or {}

        loeuf = con.get("loeuf")
        found: list[str] = []

        # ------------------------------------------------ constraint vs dependency
        if loeuf is not None and dep.get("n"):
            # EVERY RULE GETS A DENOMINATOR. Three rules share this branch and only one was
            # counting, so two of them reported a numerator with nothing under it — which is
            # the exact thing this repository refuses to publish anywhere else.
            eligible["organismal"] += 1
            eligible["cultureArtefact"] += 1
            eligible["selective"] += 1
            share = dep["dependent"] / dep["n"]
            if loeuf < T["loeufConstrained"] and share < T["selectiveLo"]:
                # Selected against in people, needed by almost no cell line.
                found.append("organismal")
            if loeuf > T["loeufTolerant"] and share > T["panShare"]:
                # Needed by nearly every line, and yet broken freely in people.
                found.append("cultureArtefact")
            if T["selectiveLo"] <= share <= T["selectiveHi"] and dep["min"] < -1.0:
                found.append("selective")

        # --------------------------------------------------- constraint vs reading
        if loeuf is not None and clin.get("total", 0) >= T["minVariants"]:
            eligible["unreadable"] += 1
            if loeuf < T["loeufConstrained"] and clin["vusShare"] > T["vusHigh"]:
                # Clearly matters; nobody can interpret its variants.
                found.append("unreadable")

        # ------------------------------------------------- expression vs dependency
        if exp.get("types") and dep.get("n"):
            eligible["broadButSelective"] += 1
            broad = exp["min"] > 0 and (exp["median"] > 0)
            share = dep["dependent"] / dep["n"]
            if broad and T["selectiveLo"] <= share <= T["selectiveHi"]:
                # On everywhere, needed by few: the shape a target programme wants.
                found.append("broadButSelective")

        # ------------------------------------------------------ damage vs structure
        # Do the pathogenic variants sit in annotated parts while the uncertain ones do not?
        feats = [f for f in (d.get("features") or [])
                 if f["kind"] in ("domain", "binding", "active")]
        hist = g.get("hist") or {}
        if feats and hist.get("pathogenic") and hist.get("uncertain") and g.get("span"):
            eligible["damageInDomains"] += 1
            span, bins = g["span"], g["bins"]
            width = span / bins
            covered = [False] * bins
            for f in feats:
                lo = max(0, int((f["start"] - 1) / width))
                hi = min(bins - 1, int((f["end"] - 1) / width))
                for b in range(lo, hi + 1):
                    covered[b] = True
            frac_covered = sum(covered) / bins
            p_in = sum(v for b, v in enumerate(hist["pathogenic"]) if covered[b])
            u_in = sum(v for b, v in enumerate(hist["uncertain"]) if covered[b])
            p_all = sum(hist["pathogenic"]) or 1
            u_all = sum(hist["uncertain"]) or 1
            # Enrichment over what the covered fraction alone would give. Both are compared
            # to the same baseline, so the claim is about the DIFFERENCE between them.
            if frac_covered and p_all >= 10 and u_all >= 10:
                p_enr = (p_in / p_all) / frac_covered
                u_enr = (u_in / u_all) / frac_covered
                if p_enr > 1.25 and p_enr > u_enr * 1.4:
                    found.append("damageInDomains")

        if found:
            per[sym] = found
            for f in found:
                counts[f] += 1

    payload = {
        "generated": "tools/gene_insights.py",
        "premise": (
            "Almost everything a person wants to know about a gene lives in a disagreement "
            "between two measurements, not inside either one. Each rule below is a stated "
            "threshold applied to every gene — not a score, not a ranking, not a composite. A "
            "reader who disagrees with a cut can see it and move it."
        ),
        "caution": (
            "Every input carries attention bias: constraint is measured where people "
            "sequenced, dependency where somebody cultured a line, variants where a clinic "
            "sent a sample, domains where a curator wrote an annotation. An intersection of "
            "two biased measurements is not less biased — it is differently biased, and no "
            "rule here can tell a real disagreement from two sampling frames. These are "
            "prompts to look, never conclusions."
        ),
        "thresholds": T,
        "rules": {
            "organismal": {
                "claim": "Under strong selection in people; needed by almost no cell line.",
                "reading": "Its importance is organismal — development, immunity, a tissue no "
                           "dish contains. A pipeline that ranks on the cell assay discards "
                           "it every time, and the assay is not silent about it, it is the "
                           "wrong instrument.",
                "rule": f"LOEUF < {T['loeufConstrained']} and dependent in "
                        f"< {T['selectiveLo']:.0%} of lines",
            },
            "cultureArtefact": {
                "claim": "Needed by nearly every line; broken freely in human populations.",
                "reading": "One of the two is wrong. Either the culture is the artefact — a "
                           "dependency of growing in plastic — or the constraint estimate is. "
                           "Worth checking before either number is quoted.",
                "rule": f"LOEUF > {T['loeufTolerant']} and dependent in "
                        f"> {T['panShare']:.0%} of lines",
            },
            "selective": {
                "claim": "Needed hard by a minority of lines.",
                "reading": "The shape a selective target has: a strong effect where it "
                           "exists, absent in most of the panel. This is what the whole "
                           "screen exists to find, and it is a shape rather than a rank.",
                "rule": f"dependent in {T['selectiveLo']:.0%}–{T['selectiveHi']:.0%} of "
                        "lines and a minimum effect below -1.0",
            },
            "unreadable": {
                "claim": "Clearly matters; its variants cannot be classified.",
                "reading": "Not an interesting mystery. A gene the field has already decided "
                           "matters and has not funded the assay for — the intersection is a "
                           "priority list nobody publishes.",
                "rule": f"LOEUF < {T['loeufConstrained']} and VUS share > "
                        f"{T['vusHigh']:.0%} over at least {T['minVariants']} variants",
            },
            "broadButSelective": {
                "claim": "Expressed across the body; needed by a minority of lines.",
                "reading": "Being on everywhere does not make a gene a poison — what a "
                           "therapy has to survive is the dependency, not the transcript.",
                "rule": f"expressed above zero in every measured cell type and dependent in "
                        f"{T['selectiveLo']:.0%}–{T['selectiveHi']:.0%} of lines",
            },
            "damageInDomains": {
                "claim": "Pathogenic variants concentrate in annotated parts; uncertain ones "
                         "do not.",
                "reading": "Weak evidence that the uncertain variants outside those parts are "
                           "tolerated — the most useful thing a positional map can say to a "
                           "curator, and it is weak on purpose: an annotated region is also a "
                           "well-studied one.",
                "rule": "pathogenic enrichment inside domains/binding/active > 1.25x, and "
                        "more than 1.4x the uncertain enrichment, over >= 10 of each",
            },
        },
        "scope": {
            "genes": len(index["genes"]),
            "withAny": len(per),
            "byRule": dict(counts),
            "eligible": dict(eligible),
        },
        "genes": per,
    }

    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"{len(per):,} of {len(index['genes']):,} genes carry at least one observation "
          f"({DEST.stat().st_size / 1024:,.0f} kB)\n")
    for rule, n in counts.most_common():
        el = eligible.get(rule, 0)
        share = f"{n / el:.1%} of {el:,} eligible" if el else "eligibility not tracked"
        print(f"  {rule:<18} {n:>6,}   {share}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
