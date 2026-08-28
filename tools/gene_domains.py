"""The parts of the protein, with their residue boundaries.

WHAT THIS ADDS, AND WHY IT WAS MISSING. The needle plot draws every reported variant at its
exact residue, which is real geometry — but on a bare line. A reader could see that damage
clusters at residue 340 and had no way to know whether residue 340 is a folded domain, a
membrane pass, or the middle of a disordered linker. The docblock said so:

    "It is not structure. There is no fold here, no domain boundary, no binding pocket —
     those need UniProt features or a solved structure, and inventing them from variant
     density would be drawing a molecule from the shape of the attention paid to it."

This fetches the UniProt features, so the needles now stand on a labelled molecule.

## What is kept, and what each is

    DOMAIN      a folded, independently stable unit with a name ("Ig-like V-type", "Kinase")
    TRANSMEM    a membrane-spanning segment — where a drug in the cytosol cannot reach
    MOTIF       a short functional sequence: a nuclear localisation signal, a cleavage site
    ACT_SITE    a single catalytic residue
    BINDING     a residue or span that holds a ligand, metal or nucleotide

These are the closest thing to an answer for "how hard is this region to operate on".
ACT_SITE and BINDING are where small molecules act; TRANSMEM is where they mostly cannot;
a variant in neither is a variant in the parts of the molecule nobody has characterised.

## THE HONEST LIMIT, and it is the same one twice

UniProt features are CURATED. A protein with no annotated domain is usually a protein nobody
has characterised, not a protein without structure — the same attention bias that the VUS
share measures, appearing again one layer down. The coverage is reported so the absence can
be read as what it is.

Run: `python tools/gene_domains.py`
"""

from __future__ import annotations

import gzip
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ontology"
OUT = ROOT / "out"
DEST = OUT / "gene_domains.json"

SRC = DATA / "uniprot_features.tsv.gz"

# UniProt writes features as "KEY start..end; /note="...""; a single-residue feature is just
# "KEY position". Both forms appear in every column.
FEATURE = re.compile(
    r'(DOMAIN|TRANSMEM|MOTIF|ACT_SITE|BINDING)\s+(\d+)(?:\.\.(\d+))?'
    r'(?:;\s*/note="([^"]*)")?'
)

KINDS = {
    "DOMAIN": "domain",
    "TRANSMEM": "membrane",
    "MOTIF": "motif",
    "ACT_SITE": "active",
    "BINDING": "binding",
}

# Per gene, so one enormous protein cannot dominate a shard.
MAX_FEATURES = 40


def main() -> int:
    if not SRC.exists():
        print(f"{SRC.relative_to(ROOT)} absent. Fetch it with:\n"
              "  curl -o data/ontology/uniprot_features.tsv.gz \\\n"
              "    'https://rest.uniprot.org/uniprotkb/stream?query=reviewed:true%20AND%20"
              "organism_id:9606&fields=gene_primary,length,ft_domain,ft_motif,ft_act_site,"
              "ft_transmem,ft_binding&format=tsv&compressed=true'")
        return 1

    index_path = OUT / "gene_index.json"
    reachable = (
        set(json.loads(index_path.read_text(encoding="utf-8"))["genes"])
        if index_path.exists() else None
    )

    genes: dict[str, dict] = {}
    kinds = Counter()
    rows = 0
    unnamed = 0

    with gzip.open(SRC, "rt", encoding="utf-8", errors="replace") as fh:
        fh.readline()
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            sym = parts[0].strip()
            if not sym:
                continue
            # UniProt lists every primary name a gene has; the first is the current symbol.
            sym = sym.split(";")[0].strip()
            if reachable is not None and sym not in reachable:
                continue
            rows += 1

            try:
                length = int(parts[1])
            except (ValueError, IndexError):
                length = 0

            found: list[dict] = []
            for chunk in parts[2:]:
                for m in FEATURE.finditer(chunk):
                    key, start, end, note = m.groups()
                    kind = KINDS[key]
                    kinds[kind] += 1
                    label = (note or "").strip()
                    if not label:
                        unnamed += 1
                    found.append({
                        "kind": kind,
                        "start": int(start),
                        "end": int(end) if end else int(start),
                        # Truncated: some notes carry a paragraph of provenance, and the
                        # track shows a label, not a citation.
                        "label": label[:70],
                    })

            if not found:
                continue
            # Left to right, so a track can be laid out in one pass without sorting in the
            # browser, and the longest first within a position so a domain does not hide
            # inside a shorter feature drawn over it.
            found.sort(key=lambda f: (f["start"], -(f["end"] - f["start"])))
            # A gene with 300 zinc-finger annotations would be one enormous record and an
            # unreadable track. The cap is stated to the reader.
            kept = found[:MAX_FEATURES]
            genes[sym] = {
                "length": length or None,
                "features": kept,
                "featureTotal": len(found),
            }

    payload = {
        "generated": "tools/gene_domains.py",
        "source": "UniProt, reviewed human proteome (Swiss-Prot)",
        "premise": (
            "Where the parts of the protein are. The needle plot draws every variant at its "
            "residue; without these the reader can see a cluster and cannot know whether the "
            "residue is a folded domain, a membrane pass, or an uncharacterised stretch."
        ),
        "caution": (
            "UniProt features are curated. A protein with no annotated domain is usually a "
            "protein nobody has characterised, not one without structure — the same "
            "attention bias the VUS share measures, one layer down."
        ),
        "kinds": {
            "domain": "a folded, independently stable unit",
            "membrane": "a membrane-spanning segment; mostly out of reach from the cytosol",
            "motif": "a short functional sequence — a localisation signal, a cleavage site",
            "active": "a catalytic residue",
            "binding": "holds a ligand, metal or nucleotide — where small molecules act",
        },
        "scope": {
            "genes": len(genes),
            "proteinsRead": rows,
            "byKind": dict(kinds.most_common()),
            "unnamedFeatures": unnamed,
            "cap": MAX_FEATURES,
        },
        "genes": genes,
    }

    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    size = DEST.stat().st_size / 1024
    print(f"{len(genes):,} genes carry at least one feature  ({size:,.0f} kB)")
    for k, n in kinds.most_common():
        print(f"  {k:<10} {n:>7,}")
    if reachable:
        print(f"\ncoverage: {len(genes):,} of {len(reachable):,} genes in the navigator "
              f"({len(genes) / len(reachable):.0%})")
    print(f"wrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
