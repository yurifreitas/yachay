"""Where to go next, from a gene.

THE PROBLEM. The navigator is a dead end. A reader arrives at NF2, reads seven layers, and
the only way out is back to the search box. But a gene is never the unit of a real question:
a curator checking NF2 wants the other genes that cause the same disease; a therapy team
wants the rest of the kinase family; someone tracing a mechanism wants the neighbours in the
graph. Every one of those is already measured here and none of them was reachable.

So each gene carries four routes out, and each says WHY it is a route — a related-genes list
with no stated relation is guesswork with a layout.

    graph        shares at least one catalogued disease with this gene. The edge comes from
                 out/rare/gene_network.json, which is built from the disease join, so the
                 relation is exactly "these two are implicated in the same condition".
    family       shares a UniProt domain family. The relation is structural: the same fold
                 doing the same job in a different protein.
    lineage      selected in the same DepMap cancer subgroup. The relation is functional and
                 came from an experiment: these cells need both.
    disease      named by the same catalogued disease, taken from the gene's own disease
                 list rather than through the graph, so the disease can be shown.

THE RANKING IS BY SHARED EVIDENCE, NOT BY SIMILARITY SCORE. There is no embedding here and
no composite. A neighbour that shares three diseases ranks above one that shares one, and
the number is shown, because a reader who disagrees with the ordering can see what produced
it.

Run after gene_index.py and gene_domains.py:  `python tools/gene_related.py`
"""

from __future__ import annotations

import json
import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DEST = OUT / "gene_related.json"

PER_ROUTE = 12
TRAILING_ORDINAL = re.compile(r"\s+\d+$")


def normalise_domain(label: str) -> str:
    return TRAILING_ORDINAL.sub("", label.split(";")[0].strip()).strip()


def main() -> int:
    index_path = OUT / "gene_index.json"
    if not index_path.exists():
        print("out/gene_index.json absent — run tools/gene_index.py first")
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    genes_in = index["genes"]

    dom = json.loads((OUT / "gene_domains.json").read_text(encoding="utf-8")) \
        if (OUT / "gene_domains.json").exists() else {"genes": {}}
    net_path = OUT / "rare" / "gene_network.json"
    net = json.loads(net_path.read_text(encoding="utf-8")) if net_path.exists() else None

    related: dict[str, dict] = defaultdict(dict)

    # ---------------------------------------------------------------- the graph
    # The edge list is CSR: indptr[i]..indptr[i+1] indexes into indices. Weights are how many
    # diseases the pair shares, which is the ranking — no similarity score is invented.
    if net:
        nodes = net["nodes"]
        indptr = net["indptr"]
        indices = net["indices"]
        weights = net.get("weights") or [1] * len(indices)
        for i, sym in enumerate(nodes):
            if sym == "-" or sym not in genes_in:
                continue
            lo, hi = indptr[i], indptr[i + 1]
            pairs = [
                (nodes[indices[j]], weights[j])
                for j in range(lo, hi)
                if nodes[indices[j]] in genes_in
            ]
            pairs.sort(key=lambda p: (-p[1], p[0]))
            if pairs:
                related[sym]["graph"] = [
                    {"gene": g, "shared": int(w)} for g, w in pairs[:PER_ROUTE]
                ]
                related[sym]["graphTotal"] = len(pairs)

    # --------------------------------------------------------------- the family
    by_family: dict[str, list[str]] = defaultdict(list)
    gene_families: dict[str, set[str]] = defaultdict(set)
    for sym, rec in dom["genes"].items():
        if sym not in genes_in:
            continue
        for f in rec.get("features", []):
            if f.get("kind") == "domain" and f.get("label"):
                name = normalise_domain(f["label"])
                if name and name not in gene_families[sym]:
                    gene_families[sym].add(name)
                    by_family[name].append(sym)

    for sym, fams in gene_families.items():
        # The smallest family a gene belongs to is the most specific thing said about it:
        # "Ig-like V-type" tells a reader more than "Protein kinase" does, and a route out
        # through the 476-member kinase family is barely a route at all.
        best = sorted(fams, key=lambda f: len(by_family[f]))[0]
        peers = [g for g in by_family[best] if g != sym]
        if peers:
            related[sym]["family"] = {
                "name": best,
                "size": len(by_family[best]),
                "genes": sorted(peers)[:PER_ROUTE],
            }

    # -------------------------------------------------------------- the lineage
    by_lineage: dict[str, list[str]] = defaultdict(list)
    for sym, rec in genes_in.items():
        for hit in rec.get("cancer", []) or []:
            if hit.get("level") == "lineage" and hit.get("subgroup"):
                by_lineage[hit["subgroup"]].append(sym)

    for sym, rec in genes_in.items():
        hits = [h for h in (rec.get("cancer") or []) if h.get("level") == "lineage"]
        if not hits:
            continue
        # The strongest effect the gene has anywhere: that is the subgroup a reader following
        # this gene is most likely to care about.
        best = max(hits, key=lambda h: h.get("d", 0.0))
        peers = [g for g in by_lineage[best["subgroup"]] if g != sym]
        if peers:
            related[sym]["lineage"] = {
                "name": best["subgroup"],
                "size": len(by_lineage[best["subgroup"]]),
                "genes": sorted(peers)[:PER_ROUTE],
            }

    # -------------------------------------------------------------- the disease
    by_disease: dict[str, list[str]] = defaultdict(list)
    disease_name: dict[str, str] = {}
    for sym, rec in genes_in.items():
        for d in rec.get("dis", []) or []:
            by_disease[d["id"]].append(sym)
            disease_name.setdefault(d["id"], d["name"])

    for sym, rec in genes_in.items():
        shared = [
            (did, [g for g in by_disease[did] if g != sym])
            for d in (rec.get("dis") or [])
            for did in [d["id"]]
        ]
        # A disease naming forty genes is a syndrome, not a lead; the tightest one is the
        # informative one.
        shared = [(did, peers) for did, peers in shared if peers]
        if not shared:
            continue
        shared.sort(key=lambda p: len(p[1]))
        did, peers = shared[0]
        related[sym]["disease"] = {
            "id": did,
            "name": disease_name.get(did, did),
            "size": len(peers) + 1,
            "genes": sorted(peers)[:PER_ROUTE],
        }

    counts = Counter()
    for rec in related.values():
        for k in ("graph", "family", "lineage", "disease"):
            if rec.get(k):
                counts[k] += 1

    payload = {
        "generated": "tools/gene_related.py",
        "premise": (
            "Four routes out of a gene, each with the relation stated. A related-genes list "
            "with no stated relation is guesswork with a layout. The ranking is shared "
            "evidence, never a similarity score: no embedding, no composite, and the number "
            "that produced the order is shown."
        ),
        "routes": {
            "graph": "shares at least one catalogued disease, from the disease-gene graph",
            "family": "shares a UniProt domain family — the same fold doing the same job",
            "lineage": "selected in the same DepMap cancer subgroup — an experiment said so",
            "disease": "named by the same catalogued disease",
        },
        "scope": {"genes": len(related), "byRoute": dict(counts), "perRoute": PER_ROUTE},
        "genes": {k: v for k, v in related.items()},
    }

    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"{len(related):,} genes have at least one route out "
          f"({DEST.stat().st_size / 1024:,.0f} kB)")
    for k, n in counts.most_common():
        print(f"  {k:<9} {n:>7,}")
    print(f"wrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
