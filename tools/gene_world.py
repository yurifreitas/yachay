"""What the world already knows about each gene, and how unevenly it knows it.

WHY A SECOND TOOL. `gene_index.py` joins what THIS repository measured. This joins what the
public catalogues on disk already hold and nothing here had ever read — four files totalling
half a gigabyte that were downloaded, used for one aggregate figure each, and never opened
per gene.

The four answer different questions, and the fourth answers a question about the other three.

## 1. What the gene IS — STRING protein info

    9606.protein.info.v12.0.txt.gz

A preferred symbol, the protein length in residues, and a functional annotation written by
curators. This is the sentence a reader wants first and the site never had: *what does this
thing do*. Nothing in `sieve` produces it, because nothing in `sieve` is about function.

## 2. HOW CONSTRAINED it is — gnomAD v4.1

    gnomad.v4.1.constraint_metrics.tsv

The best single specification of a gene's tolerance to being broken, measured across 730,000+
exomes. Three numbers are kept:

  * **LOEUF** (`lof.oe_ci.upper`) — the upper bound of the observed/expected ratio for
    loss-of-function variants. gnomAD's own recommendation is to rank on this rather than on
    pLI, because it is a bound and degrades honestly in small genes: a short gene simply
    cannot accumulate enough expected LoF to be confident, and LOEUF says so by staying high.
    Below ~0.35 is the constrained end.
  * **pLI** — probability the gene is intolerant to heterozygous LoF. Kept because it is what
    most readers have seen, and flagged as the weaker statistic it is.
  * **missense z** — the same idea for missense variation.

**The caution, and it is load-bearing.** Constraint is a population-genetic observation, not a
statement about disease. A constrained gene is one where LoF variants are selected against;
that is evidence about reproductive fitness across human history, not evidence that this gene
causes the condition in front of you. Reading LOEUF as a pathogenicity score is one of the
commonest misuses of gnomAD, and the interface says so beside the number.

## 3. WHERE IT ACTS — Human Protein Atlas single-cell RNA

    rna_single_cell_type.tsv.zip

Expression across 80+ cell types. Only the top cell types are kept, plus how many types carry
it above a floor — the difference between a gene that acts in one tissue and one that acts
everywhere, which is the scale question a therapy has to answer before anything else.

## 4. HOW UNEVENLY IT IS KNOWN — ClinVar

    variant_summary.txt.gz

Per gene: how many variants have been submitted, how they were classified, and — the number
this file exists for — **the share classified as a variant of uncertain significance.**

That share is a bias measurement, not a property of the gene. A gene with 80 % VUS is not a
mysterious gene; it is a gene whose variants nobody has had the cohort, the funding or the
functional assay to interpret. It correlates with attention, and attention correlates with
prevalence, with which populations were sequenced, and with which diseases got societies and
foundations. Publishing the VUS share beside the pathogenic count is how the interface says
"this is a statement about us, not about the gene".

Run: `python tools/gene_world.py`   (a few minutes; ClinVar is 422 MB compressed)
"""

from __future__ import annotations

import csv
import gzip
import json
import pathlib
import sys
import zipfile
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ontology"
OUT = ROOT / "out"
DEST = OUT / "gene_world.json"
WEB = ROOT / "web" / "public" / "data" / "gene_world.json"

# How many cell types to keep per gene, and the nCPM floor under which a gene is not called
# expressed. The floor is stated because it is a choice: HPA ships continuous values and
# "expressed in 40 cell types" means nothing without the cut that produced the 40.
TOP_CELLS = 8
CELL_FLOOR = 1.0


def _f(v: str) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def load_protein() -> tuple[dict[str, dict], dict]:
    """What the protein is, in one curated sentence, plus its length."""
    path = DATA / "9606.protein.info.v12.0.txt.gz"
    if not path.exists():
        return {}, {"proteins": 0, "note": "STRING protein info absent"}

    out: dict[str, dict] = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        fh.readline()  # header, commented
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            sym = parts[1].strip()
            if not sym or sym in out:
                continue
            note = parts[3].strip()
            # The annotation often opens with the protein's full name, then a semicolon, then
            # the function. Both are kept: the name is what a reader recognises and the
            # function is what they came for.
            out[sym] = {
                "size": int(parts[2]) if parts[2].isdigit() else None,
                # Capped. The full STRING annotation runs to a paragraph and the panel shows
                # a sentence; the untruncated text was two thirds of the payload.
                "note": note[:320],
            }
    return out, {"proteins": len(out), "source": "STRING v12.0"}


def load_constraint() -> tuple[dict[str, dict], dict]:
    """gnomAD constraint, canonical transcript only, LOEUF first."""
    path = DATA / "gnomad.v4.1.constraint_metrics.tsv"
    if not path.exists():
        return {}, {"genes": 0, "note": "gnomAD constraint absent"}

    out: dict[str, dict] = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            sym = (row.get("gene") or "").strip()
            if not sym:
                continue
            # One transcript per gene, and it has to be the same one every time or the numbers
            # are not comparable between genes. MANE Select first, canonical as the fallback.
            mane = (row.get("mane_select") or "").strip().lower() == "true"
            canon = (row.get("canonical") or "").strip().lower() == "true"
            if not (mane or canon):
                continue
            if sym in out and not mane:
                continue

            loeuf = _f(row.get("lof.oe_ci.upper", ""))
            rec = {
                "loeuf": round(loeuf, 3) if loeuf is not None else None,
                "oe": round(_f(row.get("lof.oe", "")) or 0.0, 3)
                      if _f(row.get("lof.oe", "")) is not None else None,
                "pLI": round(_f(row.get("lof.pLI", "")) or 0.0, 3)
                       if _f(row.get("lof.pLI", "")) is not None else None,
                "misZ": round(_f(row.get("mis.z_score", "")) or 0.0, 2)
                        if _f(row.get("mis.z_score", "")) is not None else None,
                "lofObs": int(_f(row.get("lof.obs", "")) or 0),
                "lofExp": round(_f(row.get("lof.exp", "")) or 0.0, 1),
                "mane": mane,
            }
            out[sym] = rec
    return out, {"genes": len(out), "source": "gnomAD v4.1"}


def load_expression() -> tuple[dict[str, dict], dict]:
    """Human Protein Atlas single-cell RNA: where the gene is switched on."""
    path = DATA / "rna_single_cell_type.tsv.zip"
    if not path.exists():
        return {}, {"genes": 0, "note": "HPA single-cell absent"}

    per: dict[str, list[tuple[str, float]]] = defaultdict(list)
    cell_types: set[str] = set()
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as raw:
            head = raw.readline().decode("utf-8").rstrip("\r\n").split("\t")
            i_sym = head.index("Gene name")
            i_cell = head.index("Cell type")
            i_val = head.index("nCPM")
            for line in raw:
                parts = line.decode("utf-8", "replace").rstrip("\r\n").split("\t")
                if len(parts) <= i_val:
                    continue
                v = _f(parts[i_val])
                if v is None:
                    continue
                cell_types.add(parts[i_cell])
                if v >= CELL_FLOOR:
                    per[parts[i_sym]].append((parts[i_cell], v))

    out: dict[str, dict] = {}
    for sym, rows in per.items():
        rows.sort(key=lambda r: -r[1])
        out[sym] = {
            "top": [{"cell": c, "nCPM": round(v, 1)} for c, v in rows[:TOP_CELLS]],
            # The breadth number is the point: 3 cell types and 78 cell types are different
            # kinds of gene, and a therapy aimed at the second has nowhere to hide.
            "typesAbove": len(rows),
        }
    return out, {
        "genes": len(out),
        "cellTypes": len(cell_types),
        "floor": CELL_FLOOR,
        "source": "Human Protein Atlas single-cell RNA",
    }


# ClinVar's clinical-significance strings are free text with a long tail. These are the
# buckets, and everything unmatched lands in "other" rather than being silently dropped.
def _clinsig_bucket(s: str) -> str:
    t = s.lower()
    if "conflicting" in t:
        return "conflicting"
    if "pathogenic" in t and "likely" in t:
        return "likelyPathogenic"
    if "pathogenic" in t:
        return "pathogenic"
    if "benign" in t and "likely" in t:
        return "likelyBenign"
    if "benign" in t:
        return "benign"
    if "uncertain" in t or "vus" in t:
        return "uncertain"
    return "other"


def load_clinvar() -> tuple[dict[str, dict], dict]:
    """Per gene: how many variants, how classified, and the share nobody could interpret."""
    path = DATA / "variant_summary.txt.gz"
    if not path.exists():
        return {}, {"genes": 0, "note": "ClinVar variant_summary absent"}

    counts: dict[str, Counter] = defaultdict(Counter)
    seen_alleles: dict[str, set] = defaultdict(set)
    rows = 0

    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        i_sym = head.index("GeneSymbol")
        i_sig = head.index("ClinicalSignificance")
        i_asm = head.index("Assembly")
        i_id = head.index("VariationID")
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(i_sym, i_sig, i_asm, i_id):
                continue
            # ClinVar ships one row per assembly. Counting both double-counts every variant,
            # so one assembly is picked and the choice is recorded.
            if parts[i_asm] != "GRCh38":
                continue
            sym = parts[i_sym].strip()
            if not sym or sym == "-":
                continue
            # A variant spanning several genes is listed once per gene, semicolon-joined.
            for one in sym.split(";"):
                one = one.strip()
                if not one:
                    continue
                vid = parts[i_id]
                if vid in seen_alleles[one]:
                    continue
                seen_alleles[one].add(vid)
                counts[one][_clinsig_bucket(parts[i_sig])] += 1
            rows += 1

    out: dict[str, dict] = {}
    for sym, c in counts.items():
        total = sum(c.values())
        if not total:
            continue
        out[sym] = {
            "total": total,
            "pathogenic": c["pathogenic"] + c["likelyPathogenic"],
            "benign": c["benign"] + c["likelyBenign"],
            "uncertain": c["uncertain"],
            "conflicting": c["conflicting"],
            "other": c["other"],
            # THE NUMBER THIS WHOLE LAYER EXISTS FOR. Not a property of the gene.
            "vusShare": round(c["uncertain"] / total, 4),
        }
    return out, {
        "genes": len(out),
        "rows": rows,
        "assembly": "GRCh38",
        "source": "ClinVar variant_summary",
    }


def main() -> int:
    print("reading STRING protein info…", flush=True)
    protein, p_scope = load_protein()
    print("reading gnomAD constraint…", flush=True)
    constraint, c_scope = load_constraint()
    print("reading Human Protein Atlas…", flush=True)
    expression, e_scope = load_expression()
    print("reading ClinVar (this is the slow one)…", flush=True)
    clinvar, v_scope = load_clinvar()

    # RESTRICTED TO THE GENES THE SITE CAN ACTUALLY SHOW.
    # The four sources between them name 32,910 symbols — every alias, read-through and
    # deprecated identifier the catalogues carry. Shipping all of them made an 18 MB payload
    # of which two thirds could never be reached, because the navigator only offers the genes
    # in gene_index.json. The intersection is the honest set, and the difference is reported
    # rather than silently dropped.
    index_path = OUT / "gene_index.json"
    reachable: set[str] | None = None
    if index_path.exists():
        reachable = set(json.loads(index_path.read_text(encoding="utf-8"))["genes"])

    everything = set(protein) | set(constraint) | set(expression) | set(clinvar)
    symbols = sorted(everything & reachable if reachable else everything)
    unreachable = len(everything) - len(symbols)
    genes: dict[str, dict] = {}
    for g in symbols:
        rec: dict[str, object] = {}
        if g in protein:
            rec["prot"] = protein[g]
        if g in constraint:
            rec["con"] = constraint[g]
        if g in expression:
            rec["exp"] = expression[g]
        if g in clinvar:
            rec["clin"] = clinvar[g]
        genes[g] = rec

    payload = {
        "generated": "tools/gene_world.py",
        "premise": (
            "What the public catalogues already hold about each gene, read per gene rather "
            "than in aggregate. The ClinVar VUS share is included as a measurement of "
            "attention, not of the gene: a gene whose variants nobody could interpret is a "
            "gene nobody had the cohort or the assay for."
        ),
        "scope": {
            "protein": p_scope,
            "constraint": c_scope,
            "expression": e_scope,
            "clinvar": v_scope,
            "genes": len(genes),
            "notInIndex": unreachable,
        },
        "genes": genes,
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    WEB.parent.mkdir(parents=True, exist_ok=True)
    WEB.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    size = DEST.stat().st_size / 1024
    print(f"\n{len(genes):,} genes  ({size:,.0f} kB)")
    print(f"  protein     {len(protein):>7,}")
    print(f"  constraint  {len(constraint):>7,}")
    print(f"  expression  {len(expression):>7,}  over {e_scope.get('cellTypes', 0)} cell types")
    print(f"  clinvar     {len(clinvar):>7,}  over {v_scope.get('rows', 0):,} rows")

    if clinvar:
        vus = [r["vusShare"] for r in clinvar.values() if r["total"] >= 20]
        vus.sort()
        if vus:
            med = vus[len(vus) // 2]
            print(f"\nmedian VUS share, genes with 20+ variants: {med:.1%} "
                  f"({len(vus):,} genes)")
    print(f"wrote {DEST.relative_to(ROOT)} and {WEB.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
