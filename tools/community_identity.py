#!/usr/bin/env python
"""What each community IS, tested against a control that removes the obvious explanation.

THE GAP. `community_stability.py` established that the partition is stable and
`network_layout.py` drew it. Both describe **216 blocks that have no identity**. A reader looks
at a matrix, sees structure, and learns nothing about biology — the blocks are called 0 to 215.
A grouping nobody can name is decoration with a modularity score attached.

## Why the enrichment has to be Reactome, and why phenotypes would prove nothing

The graph's edges ARE gene–disease co-membership: two genes are connected because they cause a
disease in common. So asking "do the genes in this community share diseases" is asking whether
the thing that built the edges built the edges. It would return a spectacular answer and mean
nothing. The same goes for HPO phenotype terms, which are annotations ON those diseases.

**Reactome pathways are not in that loop.** They come from curated biochemistry, not from the
disease catalogue, and nothing in the construction of this graph consulted them. If a community
assembled purely from shared diseases is also enriched for a pathway, that is a fact the
construction did not put there.

The phenotype profile is still published, because a reader wants to know what the community
looks like clinically — but it is labelled `circular_by_construction` in the payload, so it can
never be quoted as evidence for the partition.

## The control that matters

Not a random gene set. **Matched on annotation count.** Reactome coverage is wildly uneven: a
well-studied kinase sits in ninety pathways and a poorly studied gene in one, so any community
holding well-studied genes is enriched for everything at once. Drawing the null from genes
binned by how many pathways they carry removes exactly that, and it is the same length-matching
argument `gene_constraint.py` makes about LOEUF — where two thirds of the apparent effect
turned out to be the covariate.

Multiplicity is real here: 216 communities times hundreds of pathways. Benjamini–Hochberg
across the whole test family, reported as `q`, and the count that survives is the headline
rather than the count that is nominally significant.

    python tools/community_identity.py

Requires numpy and statsmodels, declared. Reads the pathway map through
tools/scale_information.py rather than reimplementing it.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import pathlib
import statistics
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

STABILITY = ROOT / "out" / "rare" / "community_stability.json"
DEST = ROOT / "out" / "rare" / "community_identity.json"

SEED = 20260831

#: Communities smaller than this are not tested. Below eight genes an enrichment is one
#: annotation away from being everything, and the multiplicity cost of testing 150 tiny
#: communities buys nothing.
MIN_COMMUNITY = 8

#: A pathway must be carried by at least this many of a community's genes to be a candidate.
MIN_HITS = 3

#: Draws behind the annotation-matched null.
DRAWS = 400


def load_scale_information():
    """Borrow the Reactome and STRING parsing that already exists, rather than writing it twice.

    `tools/scale_information.py` does its work at module level below a `__main__` guard, so it
    imports cleanly. Reimplementing `uniprot_to_symbol` here is how two files come to disagree
    about which genes exist — the failure `ontology.py` was created to end when four MONDO
    parsers had drifted apart.
    """
    spec = importlib.util.spec_from_file_location(
        "scale_information", ROOT / "tools" / "scale_information.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def all_level_pathways(symbol_of: dict[str, str]) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Gene -> every Reactome pathway it belongs to, at ANY level, with names.

    Top level would be the wrong grain here. There are 29 of them and they are filing
    categories — "Metabolism", "Disease" — so every community would come back enriched for
    Metabolism and the answer would carry no information. `scale_information.py` uses the top
    level deliberately, because it is coarse-graining an alphabet; this file is naming a group,
    which is the opposite requirement.
    """
    mapping: dict[str, set[str]] = collections.defaultdict(set)
    names: dict[str, str] = {}
    with BY_KEY["reactome_pathways"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6 or parts[5] != "Homo sapiens":
                continue
            symbol = symbol_of.get(parts[0])
            if symbol:
                mapping[symbol].add(parts[1])
                names[parts[1]] = parts[3]
    return dict(mapping), names


def disease_profile() -> dict[str, set[str]]:
    """Gene -> the diseases it is annotated to. Descriptive only: this is what built the graph."""
    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        header = next(fh, "")
        cols = header.rstrip("\n").split("\t")
        try:
            gi, di = cols.index("gene_symbol"), cols.index("disease_id")
        except ValueError:
            gi, di = 1, 0
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > max(gi, di):
                out[parts[gi]].add(parts[di])
    return dict(out)


def main() -> int:
    if not STABILITY.exists():
        print(f"missing {STABILITY} — run tools/community_stability.py first", file=sys.stderr)
        return 1

    st = json.loads(STABILITY.read_text(encoding="utf-8"))
    per = st.get("per_gene") or {}
    genes = per.get("genes", [])
    comm = per.get("community", [])
    conf = per.get("confidence", [])
    if not genes:
        print("community_stability.json carries no per_gene block", file=sys.stderr)
        return 1

    si = load_scale_information()
    pathways, names = all_level_pathways(si.uniprot_to_symbol())
    diseases = disease_profile()

    members: dict[int, list[str]] = collections.defaultdict(list)
    conf_of = dict(zip(genes, conf))
    for g, c in zip(genes, comm):
        members[int(c)].append(g)

    # The background is the graph's own genes that carry at least one pathway, not the genome.
    # Testing against the genome would measure which genes got into this catalogue, which is a
    # real finding and a different one — atlas_bias.py already reports it.
    background = [g for g in genes if pathways.get(g)]
    annotated = {g: len(pathways[g]) for g in background}
    print(f"  {len(genes)} genes in {len(members)} communities; "
          f"{len(background)} carry a Reactome pathway")

    # ANNOTATION-COUNT BINS for the matched null. Quantile bins rather than fixed widths: the
    # distribution is heavily skewed, and fixed widths would put 90% of genes in one bin and
    # make the matching a no-op.
    counts = np.array([annotated[g] for g in background])
    edges = np.unique(np.quantile(counts, np.linspace(0, 1, 9)))
    bin_of = {g: int(np.searchsorted(edges, annotated[g], side="right")) for g in background}
    by_bin: dict[int, list[str]] = collections.defaultdict(list)
    for g in background:
        by_bin[bin_of[g]].append(g)

    rng = np.random.default_rng(SEED)
    rows, tests = [], []

    for cid, mem in sorted(members.items(), key=lambda kv: -len(kv[1])):
        annotated_mem = [g for g in mem if pathways.get(g)]
        if len(annotated_mem) < MIN_COMMUNITY:
            continue

        hits = collections.Counter()
        for g in sorted(annotated_mem):
            hits.update(sorted(pathways[g]))
        # SORTED, and it is the same defect gene_constraint.py already carries a comment
        # about. `pathways[g]` is a set of strings, Python randomises string hashing per
        # process, so the Counter is built in a different order in every run. Nothing about
        # the COUNTS changes — but ties in the sort below then break differently, and the six
        # pathways published as a community's identity came out in a different order. The
        # determinism test caught it on the first run after this tool joined the suite.
        candidates = {p: hits[p] for p in sorted(hits) if hits[p] >= MIN_HITS}
        if not candidates:
            continue

        # The matched null: sets of the same size, drawn bin for bin, so the draw carries the
        # same annotation burden as the community.
        want = collections.Counter(bin_of[g] for g in annotated_mem)
        null_counts: dict[str, list[int]] = {p: [] for p in candidates}
        for _ in range(DRAWS):
            drawn: list[str] = []
            for b, k in want.items():
                pool = by_bin[b]
                idx = rng.integers(0, len(pool), size=k)
                drawn.extend(pool[i] for i in idx)
            drawn_hits = collections.Counter()
            for g in drawn:
                drawn_hits.update(sorted(pathways[g]))
            for p in candidates:
                null_counts[p].append(drawn_hits.get(p, 0))

        found = []
        for p, obs in candidates.items():
            draws = null_counts[p]
            mu = statistics.fmean(draws)
            sd = statistics.pstdev(draws)
            # The empirical tail, which is the honest quantity: with 400 draws it cannot go
            # below 1/401, and that floor is reported rather than a z extrapolated past it.
            # This is A41's rule applied at the point of writing rather than in an audit.
            ge = sum(1 for x in draws if x >= obs)
            p_emp = (ge + 1) / (DRAWS + 1)
            found.append({
                "pathway": p,
                "name": names.get(p, p),
                "genes_in_community": obs,
                "of_annotated": len(annotated_mem),
                "null_mean": round(mu, 2),
                "null_sd": round(sd, 2),
                "p_empirical": round(p_emp, 5),
                "p_floor": round(1 / (DRAWS + 1), 5),
                "fold": round(obs / mu, 2) if mu else None,
                # HOW MUCH OF THE COMMUNITY THIS ACTUALLY DESCRIBES. Ranking by significance
                # alone put "Metabolism of Angiotensinogen to Angiotensins" at the head of a
                # 482-gene community on the strength of THREE genes. The enrichment was real
                # — three against 0.27 expected — and it is not what that community is. A
                # pathway covering 0.8% of a group does not name it, and a figure that prints
                # it as the group's identity is lying with a correct p value.
                "share_of_community": round(obs / len(annotated_mem), 4),
            })
        # Significance is the gate; COVERAGE is the ordering. A pathway has to clear the null
        # to appear at all, and among those that do, the one describing most of the community
        # goes first.
        # The pathway id is the last key so the order is total: two pathways tied on
        # significance and coverage are otherwise left in whatever order they arrived, which
        # is the hash-order problem again, one level up.
        found.sort(key=lambda r: (r["p_empirical"] > 0.05, -r["genes_in_community"],
                                  r["p_empirical"], r["pathway"]))
        tests.extend(found)

        dis = collections.Counter()
        for g in sorted(mem):
            dis.update(sorted(diseases.get(g, ())))
        confs = [conf_of[g] for g in mem if conf_of.get(g) is not None]

        rows.append({
            "community": cid,
            "genes": len(mem),
            "annotated": len(annotated_mem),
            "mean_confidence": round(statistics.fmean(confs), 3) if confs else None,
            "examples": sorted(mem)[:12],
            "enriched": found[:6],
            # The single line a reader gets if they read nothing else. None when no pathway
            # both clears the null and covers a tenth of the community — which is an answer,
            # not a gap: it says this group is real and heterogeneous.
            "headline": next((e for e in found
                              if e["p_empirical"] <= 0.05 and e["share_of_community"] >= 0.1),
                             None),
            # TWO PICKS, BECAUSE COVERAGE AND SPECIFICITY PULL OPPOSITE WAYS. Ranking by
            # coverage promotes Reactome's filing categories — "Metabolism", "Immune System" —
            # which describe most of a community and say little. Ranking by fold promotes a
            # pathway found in three genes, which says a lot about almost nobody. Publishing
            # one and calling it the identity would be choosing which half to hide, so both
            # are here: the broad one names the group, the specific one says what is unusual
            # about it.
            "most_specific": max(
                (e for e in found if e["p_empirical"] <= 0.05 and e["fold"]),
                # -pathway cannot be negated, so ties go to the id that sorts first via a
                # min-style tiebreak on the reversed comparison. `max` keeps the FIRST
                # maximum it meets, so the sorted input above already makes this stable; the
                # key is explicit anyway, because relying on that is relying on a detail.
                key=lambda e: (e["fold"], e["genes_in_community"]), default=None),
            "shared_diseases": [{"disease": d, "genes": c} for d, c in dis.most_common(5)],
            "circular_by_construction": (
                "`shared_diseases` is what BUILT this graph — two genes are connected here "
                "because they cause a disease in common. It describes the community and is "
                "not evidence for it. `enriched` is the non-circular half: Reactome comes "
                "from curated biochemistry and nothing in the construction consulted it."),
        })

    # ---- multiplicity, across every test in every community -------------------------------
    surviving = 0
    if tests:
        try:
            from statsmodels.stats.multitest import multipletests
            ps = [t["p_empirical"] for t in tests]
            ok, q, _, _ = multipletests(ps, alpha=0.05, method="fdr_bh")
            for t, keep, qq in zip(tests, ok, q):
                t["q"] = round(float(qq), 5)
                t["survives_fdr"] = bool(keep)
            surviving = int(sum(ok))
        except ImportError:
            print("  statsmodels absent — q values not computed", file=sys.stderr)

    by_key = {(t["pathway"], t["genes_in_community"], t["of_annotated"]): t for t in tests}
    for r in rows:
        for e in r["enriched"]:
            t = by_key.get((e["pathway"], e["genes_in_community"], e["of_annotated"]))
            if t:
                e["q"] = t.get("q")
                e["survives_fdr"] = t.get("survives_fdr")

    named = [r for r in rows if any(e.get("survives_fdr") for e in r["enriched"])]
    # A stricter and more useful count: communities where a surviving pathway also covers at
    # least a tenth of the genes. This is the number that answers "how many of these blocks
    # can be given a name a biologist would accept".
    described = [r for r in rows
                 if r.get("headline") and r["headline"].get("survives_fdr")]

    payload = {
        "generated": "tools/community_identity.py",
        "governed_by": "docs/adr/0007 — a construct enters when a tool computes it with a "
                       "null and an interval",
        "question": ("The partition has 216 blocks called 0 to 215. What is each one, and is "
                     "the answer anything more than the way the graph was built?"),
        "why_reactome": (
            "The edges of this graph ARE gene-disease co-membership, so testing whether a "
            "community shares diseases asks whether the thing that built the edges built "
            "them. Reactome is outside that loop: curated biochemistry, consulted by nothing "
            "in the construction. An enrichment there is a fact the construction did not put "
            "in."),
        "control": (
            "Null sets of the same size drawn from the graph's own genes, MATCHED ON "
            "ANNOTATION COUNT in eight quantile bins. Reactome coverage is wildly uneven - a "
            "well-studied kinase sits in dozens of pathways - so an unmatched null would "
            "report every community holding well-studied genes as enriched for everything. "
            "Same argument as the length matching in gene_constraint.py, where two thirds of "
            "the apparent effect turned out to be the covariate."),
        "resolution": (
            "%d draws, so no empirical p below %.5f is resolved and none is reported. A z "
            "would have extrapolated past that floor, which is the failure docs/audit.md A41 "
            "found across the site." % (DRAWS, 1 / (DRAWS + 1))),
        "totals": {
            "communities_in_the_partition": len(members),
            "communities_tested": len(rows),
            "communities_with_a_named_pathway": len(named),
            "communities_a_pathway_actually_describes": len(described),
            "tests": len(tests),
            "surviving_fdr_5pct": surviving,
        },
        "says": (
            "%d of the %d communities large enough to test carry a Reactome pathway that "
            "survives a 5%% false-discovery correction against an annotation-matched null. "
            "But only %d have one that ALSO covers at least a tenth of the community, and "
            "that is the number worth quoting: a pathway found in three genes of 482 is a "
            "real enrichment and is not what the group is. The rest are stable groupings "
            "whose biology this catalogue cannot state in one line - which is a finding about "
            "the catalogue, not a failure of the clustering."
            % (len(named), len(rows), len(described))),
        "communities": rows,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"  {len(rows)} communities tested, {len(tests)} pathway tests, "
          f"{surviving} survive FDR 5%")
    print(f"  {len(named)} communities have at least one named pathway")
    print(f"  {len(described)} have one that covers a tenth of the community or more")
    for r in described[:8]:
        best = r["headline"]
        print(f"    community {r['community']:>4} ({r['genes']:>3} genes): "
              f"{best['name'][:46]:46s} {best['genes_in_community']:>3}/{best['of_annotated']:<3}"
              f" = {best['share_of_community'] * 100:4.0f}%  vs {best['null_mean']} "
              f"q={best.get('q')}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
