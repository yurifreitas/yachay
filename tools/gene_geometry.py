"""Where along the molecule the mutations fall, and what kind they are.

WHY. Every variant panel on this site was a total: 2,565 submitted, 303 pathogenic, 1,206
uncertain. Totals say how much is known. They say nothing about the thing a structural
biologist, a curator or a therapy designer actually needs, which is **where** — because a
protein is not a bag of residues. Damage concentrated in eighty residues of a binding
interface and damage spread evenly along two thousand are different diseases with different
treatments, and the counts are identical.

ClinVar already carries the position. It is in the `Name` field, in HGVS:

    NM_000268.4(NF2):c.1079T>C (p.Leu360Pro)     -> residue 360, missense
    NM_000268.4(NF2):c.169C>T (p.Arg57Ter)       -> residue 57, stop gained
    NM_000268.4(NF2):c.995del (p.Lys332fs)       -> residue 332, frameshift
    NM_000268.4(NF2):c.240+1G>T                  -> no residue: splice site

Nothing here had ever parsed it. This does, per gene, and reports four things.

## 1. The consequence spectrum — the routes by which the gene breaks

Missense, stop-gained, frameshift, splice, in-frame indel. These are not interchangeable.
A gene that breaks by stop-gained and frameshift is losing function; one that breaks almost
entirely by missense is more often losing a *specific* function, or gaining one — and that
distinction decides whether replacing the protein could possibly help.

## 2. The positional profile — the geometry

Residue positions, binned along the protein and split by clinical significance. Drawn as a
needle plot, this is the figure that shows a mutation hotspot at a glance and shows an
evenly-damaged protein just as clearly.

Positions are reported BOTH in residues and as a fraction of the protein length (from the
STRING annotation), because a hotspot at residue 400 means something different in a
450-residue protein than in a 4,500-residue one.

## 3. Clustering — is the hotspot real, or is it looking?

A hotspot in an eyeballed plot is a Rorschach test. So the concentration is measured: the
share of pathogenic variants falling in the densest tenth of the protein, against the 10 %
that a uniform spread would give. A ratio near 1 is a protein damaged everywhere.

**The confound is stated with the number.** Variant density also tracks sequencing depth and
curation attention, and exons are not sequenced equally. A cluster is evidence of a hotspot
OR of a well-studied region, and this file cannot separate them.

## 4. Pathways — the signalling context

Reactome pathway membership, joined through the STRING alias table. This is the closest
honest answer available offline to "which signalling regions does this operate in", and its
limits are stated in the panel: pathway membership is a statement about the *protein*, not
about which of its residues carry the signal.

Run after `gene_world.py`:  `python tools/gene_geometry.py`
"""

from __future__ import annotations

import gzip
import json
import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ontology"
OUT = ROOT / "out"
DEST = OUT / "gene_geometry.json"

# Three-letter amino acid codes, so a malformed HGVS string cannot be mistaken for a position.
AA = ("Ala|Arg|Asn|Asp|Cys|Gln|Glu|Gly|His|Ile|Leu|Lys|Met|Phe|Pro|Ser|Thr|Trp|Tyr|Val|"
      "Sec|Pyl|Ter|Xaa")
P_CHANGE = re.compile(rf"\(p\.({AA})(\d+)([A-Za-z*=]*)\)")
C_SPLICE = re.compile(r"c\.[-*]?\d+[+-]\d+")

# Positions are binned rather than shipped one by one: a gene with 40,000 submitted variants
# would otherwise be a megabyte on its own, and no plot resolves 40,000 needles anyway.
BINS = 60
# How many individually-named recurrent positions to keep. These are the ones a reader wants
# to see labelled — a residue hit two hundred times is a fact about the gene.
TOP_POSITIONS = 12


def _bucket(sig: str) -> str:
    t = sig.lower()
    if "conflicting" in t:
        return "conflicting"
    if "pathogenic" in t:
        return "pathogenic"
    if "benign" in t:
        return "benign"
    if "uncertain" in t:
        return "uncertain"
    return "other"


def _consequence(name: str, vtype: str) -> tuple[str, int | None]:
    """The route the variant breaks the protein by, and the residue it lands on."""
    m = P_CHANGE.search(name)
    if m:
        ref, pos, alt = m.group(1), int(m.group(2)), m.group(3)
        if alt.endswith("fs"):
            return "frameshift", pos
        if alt == "Ter" or alt == "*":
            return "stopGained", pos
        if ref == "Ter":
            return "stopLost", pos
        if alt in ("", "=") :
            return "synonymous", pos
        if alt.startswith("del") or alt.startswith("dup") or alt.startswith("ins"):
            return "inFrameIndel", pos
        return "missense", pos
    # No protein change. A c. position with an offset is intronic — splice territory.
    if C_SPLICE.search(name):
        return "splice", None
    if vtype in ("Deletion", "Duplication", "copy number loss", "copy number gain"):
        return "structural", None
    return "other", None


def main() -> int:
    world_path = OUT / "gene_world.json"
    lengths: dict[str, int] = {}
    if world_path.exists():
        world = json.loads(world_path.read_text(encoding="utf-8"))
        for sym, rec in world["genes"].items():
            size = (rec.get("prot") or {}).get("size")
            if size:
                lengths[sym] = size

    index_path = OUT / "gene_index.json"
    reachable = (
        set(json.loads(index_path.read_text(encoding="utf-8"))["genes"])
        if index_path.exists() else None
    )

    # ---------------------------------------------------------------- ClinVar
    consequence: dict[str, Counter] = defaultdict(Counter)
    positions: dict[str, list[tuple[int, str]]] = defaultdict(list)
    seen: dict[str, set] = defaultdict(set)
    parsed = 0
    unparsed = 0

    path = DATA / "variant_summary.txt.gz"
    if not path.exists():
        print("ClinVar variant_summary absent")
        return 1

    print("parsing ClinVar positions…", flush=True)
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        iN, iT, iG, iS, iA, iV = (head.index(c) for c in
                                  ("Name", "Type", "GeneSymbol", "ClinicalSignificance",
                                   "Assembly", "VariationID"))
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) <= iV or p[iA] != "GRCh38":
                continue
            syms = [x.strip() for x in p[iG].split(";") if x.strip() and x.strip() != "-"]
            if not syms:
                continue
            cons, pos = _consequence(p[iN], p[iT])
            if pos is None:
                unparsed += 1
            else:
                parsed += 1
            sig = _bucket(p[iS])
            for sym in syms:
                if reachable is not None and sym not in reachable:
                    continue
                if p[iV] in seen[sym]:
                    continue
                seen[sym].add(p[iV])
                consequence[sym][cons] += 1
                if pos is not None:
                    positions[sym].append((pos, sig))

    # ------------------------------------------------------------- per gene
    genes: dict[str, dict] = {}
    for sym, cons in consequence.items():
        pos_rows = positions.get(sym, [])
        length = lengths.get(sym)
        # The protein length has to come from somewhere trustworthy. Falling back to the
        # furthest observed variant would make the axis a function of how much was sequenced,
        # which is exactly the confound this file is trying to expose.
        span = length or (max((p for p, _ in pos_rows), default=0) or None)

        rec: dict[str, object] = {
            "consequence": dict(cons.most_common()),
            "placed": len(pos_rows),
            "length": length,
            "lengthFrom": "STRING" if length else ("observed" if span else None),
        }

        if pos_rows and span:
            width = span / BINS
            hist: dict[str, list[int]] = {
                k: [0] * BINS for k in ("pathogenic", "uncertain", "benign", "conflicting")
            }
            for p, sig in pos_rows:
                if sig not in hist:
                    continue
                b = min(BINS - 1, int((p - 1) / width)) if width else 0
                hist[sig][b] += 1
            rec["span"] = span
            rec["bins"] = BINS
            rec["hist"] = {k: v for k, v in hist.items() if any(v)}

            # Recurrent residues, pathogenic only: a residue hit many times by variants
            # nobody could classify says something about curation, not about the protein.
            recurrent = Counter(p for p, sig in pos_rows if sig == "pathogenic")
            rec["recurrent"] = [
                {"pos": p, "n": n} for p, n in recurrent.most_common(TOP_POSITIONS) if n > 1
            ]

            # CLUSTERING. Share of pathogenic variants in the densest tenth of the protein,
            # against the 10 % a uniform spread would put there.
            path_bins = hist["pathogenic"]
            total_path = sum(path_bins)
            if total_path >= 10:
                tenth = max(1, BINS // 10)
                windows = [sum(path_bins[i:i + tenth]) for i in range(BINS - tenth + 1)]
                densest = max(windows)
                rec["clustering"] = {
                    "share": round(densest / total_path, 3),
                    "expected": round(tenth / BINS, 3),
                    "ratio": round((densest / total_path) / (tenth / BINS), 2),
                    "n": total_path,
                }
        genes[sym] = rec

    # --------------------------------------------------------------- pathways
    print("joining Reactome pathways…", flush=True)
    pathway_names: dict[str, str] = {}
    r2p = DATA / "UniProt2Reactome_All_Levels.txt"
    if r2p.exists():
        with r2p.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 6 and p[5] == "Homo sapiens":
                    pathway_names.setdefault(p[1], p[3])

    protein_symbol: dict[str, str] = {}
    info = DATA / "9606.protein.info.v12.0.txt.gz"
    if info.exists():
        with gzip.open(info, "rt", encoding="utf-8", errors="replace") as fh:
            fh.readline()
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 2:
                    protein_symbol[p[0]] = p[1]

    aliases = DATA / "9606.protein.aliases.v12.0.txt.gz"
    pathways: dict[str, set] = defaultdict(set)
    if aliases.exists():
        with gzip.open(aliases, "rt", encoding="utf-8", errors="replace") as fh:
            fh.readline()
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) < 3 or p[2] != "Ensembl_Reactome":
                    continue
                sym = protein_symbol.get(p[0])
                if not sym or (reachable is not None and sym not in reachable):
                    continue
                name = pathway_names.get(p[1])
                if name:
                    pathways[sym].add((p[1], name))

    for sym, ps in pathways.items():
        rec = genes.setdefault(sym, {})
        ordered = sorted(ps, key=lambda x: x[1])
        rec["pathways"] = [{"id": i, "name": n} for i, n in ordered[:20]]
        rec["pathwayTotal"] = len(ordered)

    payload = {
        "generated": "tools/gene_geometry.py",
        "premise": (
            "Where along the protein the variants fall, by what route they break it, and how "
            "concentrated the damage is. Position is parsed from ClinVar's HGVS; protein "
            "length comes from STRING so the axis is the molecule and not the sequencing."
        ),
        "caution": (
            "Variant density tracks sequencing depth and curation attention as well as "
            "biology. A cluster is evidence of a hotspot OR of a well-studied region, and "
            "nothing here can separate the two."
        ),
        "scope": {
            "genes": len(genes),
            "withPositions": sum(1 for r in genes.values() if r.get("hist")),
            "withPathways": len(pathways),
            "positionsParsed": parsed,
            "positionsUnparsed": unparsed,
            "bins": BINS,
            "pathwaySource": "Reactome via STRING aliases",
        },
        "genes": genes,
    }

    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    size = DEST.stat().st_size / 1024

    clustered = [r["clustering"]["ratio"] for r in genes.values() if r.get("clustering")]
    clustered.sort()
    print(f"\n{len(genes):,} genes  ({size:,.0f} kB)")
    print(f"  with a positional profile   {payload['scope']['withPositions']:>7,}")
    print(f"  with Reactome pathways      {len(pathways):>7,}")
    print(f"  HGVS positions parsed       {parsed:>7,}  ({unparsed:,} carried no residue)")
    if clustered:
        print(f"\nclustering ratio (densest tenth vs uniform), {len(clustered):,} genes:")
        print(f"  median {clustered[len(clustered) // 2]:.2f}x · "
              f"90th pct {clustered[int(len(clustered) * 0.9)]:.2f}x · "
              f"max {clustered[-1]:.2f}x")
    print(f"wrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
