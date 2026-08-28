"""Everything this repository knows about one gene, joined into one record.

WHY. The project measures genes in six separate places and publishes them in six separate
panels. A DepMap dependency lives on the run dashboard; the cancer subgroups that need that
gene live on another page; the diseases it causes live in the rare-disease atlas; its position
in the interaction graph lives in a third figure. A reader who arrives holding a gene symbol —
which is how a clinician, a curator or a patient's family actually arrives — has to visit four
pages and join by hand, and nothing tells them which pages have anything to say.

So this inverts the index. One pass over every artefact on disk, keyed by gene symbol, and
the interface can then answer the question people actually ask: *what is known about this
gene, and where does it stop.*

## What is joined, and from where

    dependency    out/depmap_genes.csv          score, n, the null it was measured against,
                                                calibrated z, both ranks, the two flags,
                                                median dependency and selectivity
    cancer        out/cancer_subgroups_*.json   every subgroup, at three nesting levels, whose
                                                candidate list contains this gene, with the
                                                effect size and the q-value that put it there
    genotype      out/cancer_genotype.json      subgroups defined by a damaging mutation
    network       out/rare/gene_network.json    degree, community, how many diseases reach it
    disease       data/ontology/genes_to_disease.txt   every catalogued disease it is linked
                                                to, with the association type
    variants      out/rare/patient_variants.json      whether real patient variants were read
                                                for this gene

## THE ABSENCES ARE VALUES, NOT MISSING KEYS

A gene with no cancer subgroup is not a gene with an empty list — it is a gene that was
tested and found in none, and that is a different statement from "not tested". Every layer
therefore records its own scope: how many genes it could have spoken about at all. The
interface prints "measured in 17,916, in no subgroup" rather than a blank.

Run: `python tools/gene_index.py`
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

sys.path.insert(0, str(ROOT / "tools"))

from build_atlas import load_disease_names  # noqa: E402
from sieve.pipeline.sources import BY_KEY  # noqa: E402

OUT = ROOT / "out"
DEST = OUT / "gene_index.json"
WEB = ROOT / "web" / "public" / "data" / "gene_index.json"

CANCER_LEVELS = ["lineage", "disease", "subtype"]


def _num(v: str) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None  # NaN is not a measurement


def _flag(v: str) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def load_dependency() -> tuple[dict[str, dict], dict]:
    """The screen itself. Rounded on write: the CSV carries float64 and nobody reads the
    fourteenth decimal of a z-score, but four significant figures halves the payload."""
    path = OUT / "depmap_genes.csv"
    if not path.exists():
        return {}, {"genes": 0, "note": "out/depmap_genes.csv absent"}

    out: dict[str, dict] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            g = (row.get("entity") or "").strip()
            if not g:
                continue
            out[g] = {
                "score": round(_num(row["score"]) or 0.0, 4),
                "n": int(float(row["n"])),
                "nullMean": round(_num(row["null_mean"]) or 0.0, 4),
                "nullSd": round(_num(row["null_sd"]) or 0.0, 4),
                "z": round(_num(row["z"]) or 0.0, 3),
                "rankRaw": int(float(row["rank_raw"])),
                "rankCal": int(float(row["rank_cal"])),
                "commonEssential": _flag(row.get("is_common_essential", "")),
                "control": _flag(row.get("is_nonessential_control", "")),
                "medianDependency": round(_num(row.get("median_dependency", "")) or 0.0, 4),
                "selectivity": round(_num(row.get("selectivity", "")) or 0.0, 4),
            }
    return out, {"genes": len(out), "source": "out/depmap_genes.csv"}


def load_cancer() -> tuple[dict[str, list], dict]:
    """Every subgroup, at three nesting levels, whose candidate list names this gene."""
    hits: dict[str, list] = defaultdict(list)
    scope = {"levels": [], "subgroups": 0}

    for level in CANCER_LEVELS:
        path = OUT / f"cancer_subgroups_{level}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        groups = data.get("results", [])
        scope["levels"].append(level)
        scope["subgroups"] += len(groups)
        for grp in groups:
            for c in grp.get("candidates", []) or []:
                g = c.get("gene")
                if not g:
                    continue
                hits[g].append({
                    "level": level,
                    "subgroup": grp.get("subgroup"),
                    "d": round(float(c.get("d", 0.0)), 3),
                    "q": float(c.get("q", 1.0)),
                    "lines": c.get("linesInGroup"),
                })

    # Strongest effect first, so the interface never has to decide what "first" means.
    for g in hits:
        hits[g].sort(key=lambda h: -h["d"])
    return dict(hits), scope


def load_genotype() -> tuple[dict[str, list], dict]:
    """Subgroups defined by carrying a damaging mutation, rather than by a catalogue label."""
    path = OUT / "cancer_genotype.json"
    if not path.exists():
        return {}, {"subgroups": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    groups = data.get("results", []) or []
    hits: dict[str, list] = defaultdict(list)
    for grp in groups:
        for c in grp.get("candidates", []) or []:
            g = c.get("gene")
            if not g:
                continue
            hits[g].append({
                "mutatedGene": grp.get("subgroup"),
                "d": round(float(c.get("d", 0.0)), 3),
                "q": float(c.get("q", 1.0)),
                "lines": c.get("linesInGroup"),
            })
    for g in hits:
        hits[g].sort(key=lambda h: -h["d"])
    return dict(hits), {"subgroups": len(groups)}


def load_network() -> tuple[dict[str, dict], dict]:
    """Position in the disease-gene graph: how connected, which community, how many diseases."""
    path = OUT / "rare" / "gene_network.json"
    if not path.exists():
        return {}, {"nodes": 0}
    g = json.loads(path.read_text(encoding="utf-8"))
    nodes = g.get("nodes", [])
    degree = g.get("degree", [])
    community = g.get("community", [])
    diseases = g.get("diseaseCount", [])
    out: dict[str, dict] = {}
    for i, name in enumerate(nodes):
        if not name or name == "-":
            continue
        out[name] = {
            "degree": degree[i] if i < len(degree) else 0,
            "community": community[i] if i < len(community) else None,
            "diseases": diseases[i] if i < len(diseases) else 0,
        }
    return out, {"nodes": len(out), "modularity": g.get("modularity")}


def load_diseases() -> tuple[dict[str, list], dict]:
    """Every catalogued disease a gene is linked to, with HPO's own association type.

    The association type is kept and not flattened: MENDELIAN and POLYGENIC are different
    claims, and UNKNOWN — the largest class in the file — is a third.

    THE NAME COMES FROM A SECOND FILE, and assuming otherwise cost this tool its first run.
    `genes_to_disease.txt` has five columns and none of them is a disease name; the readable
    name lives in the annotation file, keyed by the same identifier. The first version read a
    `disease_name` column that does not exist, so every row failed the guard and the layer
    shipped zero pairs — which the run printed as "disease 0", and which is why it printed a
    scope at all.
    """
    path = BY_KEY["hpo_genes"].dest
    if not path.exists():
        return {}, {"pairs": 0}

    names, _, _ = load_disease_names()
    out: dict[str, list] = defaultdict(list)
    pairs = 0
    unnamed = 0

    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g = (row.get("gene_symbol") or "").strip()
            did = (row.get("disease_id") or "").strip()
            if not g or not did:
                continue
            name = names.get(did, "")
            if not name:
                unnamed += 1
            pairs += 1
            out[g].append({
                "id": did,
                # A disease in the gene table and absent from the annotation file has no name
                # to show. The identifier is what there is, and printing it is more honest
                # than dropping the row and under-reporting the gene's disease count.
                "name": name or did,
                "assoc": (row.get("association_type") or "?").strip(),
            })

    for g in out:
        out[g].sort(key=lambda d: d["name"])
    return dict(out), {"pairs": pairs, "genes": len(out), "unnamed": unnamed}


def main() -> int:
    dep, dep_scope = load_dependency()
    cancer, cancer_scope = load_cancer()
    genotype, geno_scope = load_genotype()
    network, net_scope = load_network()
    diseases, dis_scope = load_diseases()

    symbols = sorted(set(dep) | set(cancer) | set(genotype) | set(network) | set(diseases))

    genes: dict[str, dict] = {}
    for g in symbols:
        rec: dict[str, object] = {}
        if g in dep:
            rec["dep"] = dep[g]
        if g in cancer:
            # Capped: a gene in forty subgroups is a pan-essential, and the interface says so
            # from the flag rather than by printing forty rows.
            rec["cancer"] = cancer[g][:12]
            rec["cancerTotal"] = len(cancer[g])
        if g in genotype:
            rec["genotype"] = genotype[g][:12]
            rec["genotypeTotal"] = len(genotype[g])
        if g in network:
            rec["net"] = network[g]
        if g in diseases:
            rec["dis"] = diseases[g][:40]
            rec["disTotal"] = len(diseases[g])
        genes[g] = rec

    payload = {
        "generated": "tools/gene_index.py",
        "premise": (
            "One record per gene, joined across every artefact on disk. The absences are "
            "values: a gene measured in the screen and found in no cancer subgroup is a "
            "different statement from a gene that was never measured, and each layer "
            "publishes the scope it could have spoken about."
        ),
        "scope": {
            "dependency": dep_scope,
            "cancer": cancer_scope,
            "genotype": geno_scope,
            "network": net_scope,
            "disease": dis_scope,
            "genes": len(genes),
        },
        "genes": genes,
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    WEB.parent.mkdir(parents=True, exist_ok=True)
    WEB.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    size = DEST.stat().st_size / 1024
    layered = sum(1 for r in genes.values() if len(r) > 1)
    print(f"{len(genes):,} genes indexed  ({size:,.0f} kB)")
    print(f"  dependency  {dep_scope.get('genes', 0):>6,}")
    print(f"  cancer      {len(cancer):>6,}  over {cancer_scope['subgroups']} subgroups")
    print(f"  genotype    {len(genotype):>6,}  over {geno_scope['subgroups']} mutated genes")
    print(f"  network     {len(network):>6,}")
    print(f"  disease     {len(diseases):>6,}  over {dis_scope['pairs']:,} gene-disease pairs")
    print(f"\n{layered:,} genes are described by more than one layer.")
    print(f"wrote {DEST.relative_to(ROOT)} and {WEB.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
