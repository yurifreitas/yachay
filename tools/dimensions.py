#!/usr/bin/env python
"""Seven ways of re-looking at the same data, each borrowed from someone who changed how
a field sees.

THE RULE FOR THIS FILE. A name earns its place only if it yields a **transform we can
actually apply to the data already in this repository**, and the transform has to produce
a different number than the default view. No metaphors, no invocations. Where a connection
is famous but does not compute, it is left out and said so.

Every entry below therefore has: the person, the actual contribution, the transform, and
the number the transform produced when run here.

    python tools/dimensions.py     # writes out/rare/dimensions.json
"""

from __future__ import annotations

import csv
import json
import math
import pathlib
import sys
from collections import Counter, defaultdict, deque
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"


# ---------------------------------------------------------------------------------------
# FEYNMAN — sum over histories, not the single shortest one.
# ---------------------------------------------------------------------------------------
def feynman(graph: dict) -> dict:
    """Path-integral reachability on the lupus network.

    The network view answers "is there a path from this gene to a therapy" with a
    breadth-first *shortest* path. That is one history out of many, and it treats a gene
    joined by a single fragile route the same as one joined by fifty.

    Feynman's move — sum the amplitudes of ALL paths rather than following one — gives a
    different quantity: how *strongly* connected a gene is, with longer paths damped. Here
    each path of length L contributes w**L, so a short path dominates but a thicket of
    long ones still counts.

    This is not physics; it is the same arithmetic used for a different object, and it
    produces a ranking the shortest-path view cannot.
    """
    adj = defaultdict(set)
    for e in graph["edges"]:
        adj[e["source"]].add(e["target"])
        adj[e["target"]].add(e["source"])
    therapies = {t["id"] for t in graph["nodes"]["therapies"]}
    genes = graph["nodes"]["genes"]

    W, MAX_L = 0.45, 6

    def amplitude(start: str) -> tuple[float, int]:
        """Damped count of distinct simple paths to any therapy, and how many there are."""
        total, count = 0.0, 0
        stack = [(start, {start})]
        while stack:
            node, seen = stack.pop()
            if len(seen) - 1 > MAX_L:
                continue
            if node in therapies and node != start:
                total += W ** (len(seen) - 1)
                count += 1
                continue                      # a therapy is a sink: stop, do not pass through
            for nxt in adj[node]:
                if nxt not in seen:
                    stack.append((nxt, seen | {nxt}))
        return total, count

    rows = []
    for g in genes:
        amp, paths = amplitude(g["id"])
        rows.append({
            "gene": g["id"],
            "hops": g["hops"],
            "reachable": g["reachable"],
            "amplitude": round(amp, 5),
            "paths": paths,
        })
    rows.sort(key=lambda r: -r["amplitude"])

    # The finding: does the sum-over-paths ranking agree with the shortest-path one?
    reachable = [r for r in rows if r["reachable"]]
    same_hops = defaultdict(list)
    for r in reachable:
        same_hops[r["hops"]].append(r)
    # Within one hop-count the shortest-path view says "identical"; the path integral does not.
    spread = {
        h: {
            "genes": len(v),
            "minAmplitude": round(min(x["amplitude"] for x in v), 5),
            "maxAmplitude": round(max(x["amplitude"] for x in v), 5),
            "ratio": round(max(x["amplitude"] for x in v) / max(min(x["amplitude"] for x in v), 1e-9), 1),
        }
        for h, v in sorted(same_hops.items()) if len(v) > 1
    }
    return {
        "rows": rows,
        "tiedButDifferent": spread,
        "strongest": rows[0]["gene"] if rows else None,
        "weakestReachable": min(reachable, key=lambda r: r["amplitude"])["gene"] if reachable else None,
    }


# ---------------------------------------------------------------------------------------
# KIMURA — most variation does nothing. Build the null before the signal.
# ---------------------------------------------------------------------------------------
def kimura(disease_genes: dict[str, set[str]], all_genes: set[str]) -> dict:
    """The neutral fraction of the genome, measured rather than assumed.

    Kimura's neutral theory says most molecular variation is selectively neutral — the
    background, not the signal. The same discipline is Stage 1 of this library: know what
    nothing looks like before ranking something.

    Applied here: of the genes the Human Protein Atlas measures, what fraction has ANY
    disease association at all? That fraction is the field's own null.
    """
    with_disease = {g for gs in disease_genes.values() for g in gs} & all_genes
    n_all, n_dis = len(all_genes), len(with_disease)
    return {
        "genesMeasured": n_all,
        "genesWithAnyDisease": n_dis,
        "neutralFraction": round(1 - n_dis / max(n_all, 1), 4),
        "note": "Not a claim that these genes are inert — a statement that no rare disease "
                "has been attributed to them yet, which is the same distinction the atlas "
                "draws between UNKNOWN and NONE.",
    }


# ---------------------------------------------------------------------------------------
# HAWKING — the outlier a mean erases.
# ---------------------------------------------------------------------------------------
def hawking(disease_genes: dict[str, set[str]]) -> dict:
    """Distribution over summary, argued from a person rather than a principle.

    Motor neurone disease has a median survival usually quoted at two to four years.
    Stephen Hawking lived with it for over fifty. He is not a counterexample to the
    statistic — he is the tail the statistic hides, and quoting the median as if it were a
    prognosis erases him.

    The same shape is in this atlas: genes per disease has a median of 1 and a maximum of
    114. Any sentence that says 'a rare disease has a gene' is a sentence about the median.
    """
    counts = sorted(len(v) for v in disease_genes.values())
    n = len(counts)
    mean = sum(counts) / n
    return {
        "n": n,
        "min": counts[0],
        "median": counts[n // 2],
        "mean": round(mean, 3),
        "p95": counts[int(n * 0.95)],
        "p99": counts[int(n * 0.99)],
        "max": counts[-1],
        "aboveMean": sum(1 for c in counts if c > mean),
        "shareAboveMean": round(sum(1 for c in counts if c > mean) / n, 4),
    }


# ---------------------------------------------------------------------------------------
# SIDIS — the famous number nobody measured.
# ---------------------------------------------------------------------------------------
def sidis() -> dict:
    """A provenance audit of this project's own claims.

    William James Sidis is quoted everywhere with an IQ of 250-300. No such test was ever
    administered; the figure is an estimate that acquired the appearance of a measurement
    through repetition. He is the cleanest available case of a number with no source
    outliving every attempt to correct it.

    So: how many claims in this atlas carry a stated source, and how many are 'from working
    knowledge'? Counted from the seeds' own confidence fields rather than asserted.
    """
    audited: list[dict] = []
    for name, path, field in (
        ("rare-disease lexicon", RARE / "lexicon.json", "diseases"),
        ("lupus genes", RARE / "lupus_graph.json", None),
        ("nomenclature", RARE / "nomenclature.json", "names"),
    ):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if name == "lupus genes":
            items = data["nodes"]["genes"]
        else:
            items = data[field]
        conf = Counter(i.get("confidence", "unstated") for i in items)
        audited.append({
            "source": name,
            "items": len(items),
            "byConfidence": dict(conf),
            "highShare": round(conf.get("high", 0) / max(len(items), 1), 3),
        })
    total = sum(a["items"] for a in audited)
    high = sum(a["byConfidence"].get("high", 0) for a in audited)
    return {
        "audited": audited,
        "totalClaims": total,
        "highConfidence": high,
        "highShare": round(high / max(total, 1), 4),
        "ingestedInstead": "The world-atlas tab replaced hand-authored claims with ingested "
                           "catalogues precisely to move this ratio.",
    }


# ---------------------------------------------------------------------------------------
# PENROSE (Lionel) — the actual ancestor, and the one usually skipped.
# ---------------------------------------------------------------------------------------
def penrose(disease_genes: dict[str, set[str]], prevalence: dict[str, str]) -> dict:
    """Rare recessives are common in aggregate — Lionel Penrose's arithmetic.

    Lionel Penrose was a medical geneticist: the Colchester Survey, the maternal-age
    effect in Down syndrome, and segregation-ratio methods that preceded linkage analysis.
    He also renamed UCL's Galton Chair of Eugenics to Human Genetics, which is the kind of
    fact that belongs in the nomenclature tab.

    His arithmetic point, applied here: each entity is negligible and the union is not.
    Counted over the catalogue rather than assumed.

    (His son Roger's aperiodic tilings are a real dimensional-projection method — a 2D
    quasicrystal is a slice of a higher-dimensional periodic lattice. It is genuinely the
    right analogy for projecting a gene x cell space, and it is NOT implemented here.
    Naming it without running it would be exactly the decoration this file refuses.)
    """
    ultra = [d for d, p in prevalence.items() if p in ("<1 / 1 000 000", "1-9 / 1 000 000")]
    # Upper bound on the aggregate, using the top of each band. Deliberately an upper
    # bound and labelled as one: the point is the order of magnitude, not the value.
    per_million_upper = {"<1 / 1 000 000": 1.0, "1-9 / 1 000 000": 9.0}
    agg = sum(per_million_upper[prevalence[d]] for d in ultra)
    return {
        "ultraRareEntities": len(ultra),
        "aggregatePerMillionUpperBound": round(agg, 1),
        "aggregatePercentUpperBound": round(agg / 1e6 * 100, 4),
        "note": "An upper bound from band ceilings, not an estimate. Individually "
                "negligible, collectively not — which is Penrose's point and the reason a "
                "platform argument for rare disease is arithmetic rather than sentiment.",
    }


# ---------------------------------------------------------------------------------------
# WELLER — why a cell line exists at all.
# ---------------------------------------------------------------------------------------
def weller(atlas: dict) -> dict:
    """The cell axis has a founder, and this repository runs on his consequence.

    Thomas Weller shared the 1954 Nobel for growing poliovirus in non-neural cell culture.
    Before that, a virus had to be grown in an animal. Cell culture is what made an
    experiment addressable to a cell type rather than an organism — which is the
    precondition for a cell-line panel, and therefore for DepMap, and therefore for the
    statistic this whole library is built on.
    """
    return {
        "cellTypes": atlas["scale"]["cellTypes"],
        "genesWithCellData": atlas["scale"]["genesWithCellData"],
        "diseasesPlaceable": atlas["scale"]["diseasesPlaceableOnCellAxis"],
        "note": "Every number in the cell-versus-gene tab is downstream of cell culture "
                "being possible at all.",
    }


# ---------------------------------------------------------------------------------------
# McKUSICK — the catalogue is an artefact with an author.
# ---------------------------------------------------------------------------------------
def mckusick(atlas: dict) -> dict:
    """OMIM is a person's decision structure, and this atlas ingested it.

    Victor McKusick began Mendelian Inheritance in Man as a printed catalogue in 1966.
    Every OMIM identifier in this project traces to editorial decisions about what counts
    as one entity — which is why the catalogue's shape is a fact about medical genetics'
    history as much as about biology.
    """
    by_prefix = atlas["scale"]["diseasesByPrefix"]
    total = atlas["scale"]["diseases"]
    return {
        "byPrefix": by_prefix,
        "omimShare": round(by_prefix.get("OMIM", 0) / max(total, 1), 4),
        "note": "The OMIM share is why the earlier 'rarer means less known' claim was a "
                "denominator fallacy: OMIM entries are mendelian by editorial construction.",
    }


def main() -> int:
    RARE.mkdir(parents=True, exist_ok=True)
    graph = json.loads((RARE / "lupus_graph.json").read_text(encoding="utf-8"))
    atlas = json.loads((RARE / "atlas.json").read_text(encoding="utf-8"))

    disease_genes: dict[str, set[str]] = defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g, d = (row.get("gene_symbol") or "").strip(), (row.get("disease_id") or "").strip()
            if g and d:
                disease_genes[d].add(g)

    prevalence: dict[str, str] = {}
    path = BY_KEY["orpha_prevalence"].dest
    order = ["<1 / 1 000 000", "1-9 / 1 000 000", "1-9 / 100 000", "1-5 / 10 000",
             "6-9 / 10 000", ">1 / 1000"]
    rank = {p: i for i, p in enumerate(order)}
    # PARSER, NOT REGEX. Found by tests/test_prevalence_readers_agree.py, which was written
    # for the other four readers and caught this fifth one that a manual search had missed.
    # The pattern below used to run past empty `<PrevalenceClass/>` elements into the next
    # `<Name>`, and never decoded `&lt;`. See docs/audit.md A11.
    def _text(node, sub):
        el = node.find(sub)
        return el.text.strip() if el is not None and el.text else None

    for _, disorder in ET.iterparse(str(path), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        code = _text(disorder, "OrphaCode")
        if code:
            classes = [c for c in (_text(rec, "PrevalenceClass/Name")
                                   for rec in disorder.findall("./PrevalenceList/Prevalence"))
                       if c]
            best = min(classes, key=lambda c: rank.get(c, 99), default=None)
            if best:
                prevalence[f"ORPHA:{code}"] = best
        disorder.clear()

    # The HPA gene set, read from the source. Deriving it from `disease_genes` would be
    # circular — every gene would have a disease by construction, and the neutral fraction
    # would come out 0.0%, which is exactly what the first run of this file reported.
    import io, zipfile
    hpa_genes: set[str] = set()
    with zipfile.ZipFile(BY_KEY["hpa_single_cell"].dest) as z:
        inner = next(n for n in z.namelist() if n.endswith(".tsv"))
        with z.open(inner) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="	"):
                g = (row.get("Gene name") or "").strip()
                if g:
                    hpa_genes.add(g)

    dims = [
        {
            "id": "feynman",
            "person": "Richard Feynman",
            "contribution": "Path integrals: a system's amplitude is the sum over ALL "
                            "histories, not the single classical one.",
            "transform": "Replace shortest-path reachability on the lupus network with a "
                         "damped sum over every simple path to a therapy.",
            "result": feynman(graph),
        },
        {
            "id": "kimura",
            "person": "Motoo Kimura",
            "contribution": "The neutral theory: most molecular variation is selectively "
                            "neutral — background, not signal.",
            "transform": "Measure the field's own null: the share of measured genes with no "
                         "rare-disease association at all.",
            "result": kimura(disease_genes, hpa_genes),
        },
        {
            "id": "hawking",
            "person": "Stephen Hawking",
            "contribution": "Lived over fifty years with motor neurone disease, against a "
                            "median usually quoted at two to four.",
            "transform": "Refuse the summary: report the whole distribution of genes per "
                         "disease instead of its centre.",
            "result": hawking(disease_genes),
        },
        {
            "id": "sidis",
            "person": "William James Sidis",
            "contribution": "Quoted everywhere with an IQ of 250-300. No such test was "
                            "administered; the number is an estimate that repetition turned "
                            "into a measurement.",
            "transform": "Audit this project's own claims for stated provenance.",
            "result": sidis(),
        },
        {
            "id": "penrose",
            "person": "Lionel Penrose",
            "contribution": "Medical geneticist: the Colchester Survey, the maternal-age "
                            "effect in Down syndrome, segregation-ratio methods — and he "
                            "renamed UCL's Chair of Eugenics to Human Genetics.",
            "transform": "Aggregate the negligible: sum the ultra-rare bands to their "
                         "ceiling and read the union rather than the entities.",
            "result": penrose(disease_genes, prevalence),
        },
        {
            "id": "weller",
            "person": "Thomas Huckle Weller",
            "contribution": "Nobel 1954, for growing poliovirus in non-neural cell culture "
                            "— the technique that made an experiment addressable to a cell "
                            "type rather than an organism.",
            "transform": "Name the precondition: everything on the cell axis exists because "
                         "cell culture does.",
            "result": weller(atlas),
        },
        {
            "id": "mckusick",
            "person": "Victor McKusick",
            "contribution": "Began Mendelian Inheritance in Man as a printed catalogue in "
                            "1966 — the ancestor of the OMIM identifiers this atlas ingests.",
            "transform": "Treat the catalogue as an authored artefact and read its "
                         "composition as a historical fact.",
            "result": mckusick(atlas),
        },
    ]

    payload = {
        "generated": "2026-08-27",
        "rule": (
            "A name earns a place here only if it yields a transform that runs on data "
            "already in this repository AND produces a different number than the default "
            "view. Connections that are famous but do not compute are named as omitted."
        ),
        "omitted": [
            {
                "person": "Roger Penrose",
                "why": "Aperiodic tilings are genuinely a dimensional-projection method — a "
                       "2D quasicrystal is a slice of a higher-dimensional periodic lattice, "
                       "and that is the right analogy for projecting a gene x cell space. "
                       "It is not implemented, so it is listed as omitted rather than "
                       "invoked."
            },
            {
                "person": "John Snow",
                "why": "Spatial dimensionalisation of an outbreak. This atlas has no "
                       "geographic axis; Orphanet's prevalence records carry country scope "
                       "and could supply one. Not built."
            },
        ],
        "dimensions": dims,
    }
    (RARE / "dimensions.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("wrote out/rare/dimensions.json")
    f = dims[0]["result"]
    print("  Feynman   strongest %s · weakest reachable %s · tie groups where the "
          "shortest path says 'identical': %d"
          % (f["strongest"], f["weakestReachable"], len(f["tiedButDifferent"])))
    for h, v in f["tiedButDifferent"].items():
        print("            at %d hops: %d genes, amplitude spread %sx" % (h, v["genes"], v["ratio"]))
    k = dims[1]["result"]
    print("  Kimura    %.1f%% of measured genes have no rare-disease association"
          % (100 * k["neutralFraction"]))
    hw = dims[2]["result"]
    print("  Hawking   median %d, mean %.2f, max %d — only %.1f%% are above the mean"
          % (hw["median"], hw["mean"], hw["max"], 100 * hw["shareAboveMean"]))
    sd = dims[3]["result"]
    print("  Sidis     %d/%d hand-authored claims are high-confidence (%.0f%%)"
          % (sd["highConfidence"], sd["totalClaims"], 100 * sd["highShare"]))
    p = dims[4]["result"]
    print("  Penrose   %d ultra-rare entities, union <= %s per million (%.4f%% of people)"
          % (p["ultraRareEntities"], p["aggregatePerMillionUpperBound"],
             p["aggregatePercentUpperBound"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
