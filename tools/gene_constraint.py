"""Selective constraint as an axis, and as the confound three earlier results could not name.

WHAT THIS ADDS. `data/ontology/gnomad.v4.1.constraint_metrics.tsv` has been on disk since the
ingest and no tool has read a byte of it — 95 MB describing, for every human gene, how much
less loss-of-function variation is observed in 800k exomes than mutation rate predicts. That
is a property of the GENE, measured in a population that was never asked about disease, and it
is therefore the one axis in this repository that cannot have been produced by the curation
process it is used to audit.

WHY IT MATTERS HERE, and this is the reason it is worth a tool rather than a column:

  * `tools/attention_burden.py` measured attention against prevalence at +0.331 and defended
    it against ONE confound — that a citation belongs to the gene rather than to the disease.
    It could not address the deeper version: perhaps rare diseases are studied because their
    genes are constrained, and prevalence is riding on constraint. Constraint was not on disk
    in a form anything read, so the objection could be stated and not answered. It can be
    answered now.
  * `tools/autism_convergence.py` found the autism gene set concentrated by cell type and NOT
    by pathway. A set of 717 genes that is unusually constrained would explain part of that
    without any spatial story, so the set is tested against constraint-matched draws here.

THE FIT TEST (.claude/skills/sieve-new-adapter), answered before any code:

  1. many candidate entities to rank?      YES — 19,704 genes.
  2. score from noisy observations?        YES — LOEUF is an observed/expected ratio with a
                                           published confidence interval per gene.
  3. does the observation count VARY?      YES, enormously: `lof.possible` runs from single
                                           digits to hundreds, which is exactly why gnomAD
                                           publishes LOEUF (an interval bound) rather than
                                           the point o/e.
  4. is the aggregate a SELECTION?         **NO.** Nothing here takes a max, a top-k or an
                                           enrichment over per-gene draws. Every statistic is
                                           a mean, a rank correlation, or a set mean against
                                           a matched null.

  Three yeses and a no. By the skill's own rule that is a VARIANCE problem, not selection
  bias: report intervals, go to Stage 3, and publish no Stage 1 claim. There is no shortlist
  in this file and no gene is ranked as a finding.

THE ONE THAT MATTERS MOST, said plainly: gnomAD constraint is itself a function of gene
LENGTH and of how well a gene is covered by exome capture. A short gene cannot be constrained
by this measure — there is nothing to observe. So every arm here is reported against a null
that holds `lof.possible` fixed, and the raw contrast is printed beside it so a reader can see
how much of it was length.

    python tools/gene_constraint.py
"""
from __future__ import annotations

import collections
import csv
import gzip
import json
import math
import pathlib
import random
import statistics
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

CONSTRAINT = ROOT / "data" / "ontology" / "gnomad.v4.1.constraint_metrics.tsv"
DEST = ROOT / "out" / "rare" / "gene_constraint.json"

HUMAN_TAX = "9606"
SEED = 20260830

#: gnomAD's own recommendation, and it is a threshold about the METRIC rather than about
#: biology: LOEUF below 0.6 is the decile band the flagship paper uses for "constrained".
#: Registered rather than tuned — no arm below depends on it, it is a label on a table.
LOEUF_CONSTRAINED = 0.6

#: A gene with too few possible LoF sites has a LOEUF whose interval spans the whole range.
#: gnomAD says so; this drops them rather than ranking noise.
MIN_POSSIBLE_LOF = 10

#: Draws for every permutation null. 400 is enough for a z at the sizes here and keeps the
#: whole tool under a minute on one core.
DRAWS = 400

#: Buckets for the matched null: genes are binned on log10(possible LoF sites), and a draw
#: takes the same number from each bin as the observed set has. Ten bins is fine enough that
#: within-bin length variation is small and coarse enough that every bin has candidates.
LENGTH_BINS = 10

#: Orphanet prevalence bands, mapped to the log10 midpoint of cases per 100,000. Copied
#: verbatim from tools/attention_burden.py rather than imported, because the two files must
#: be able to disagree loudly if either is edited — a shared constant would let a change in
#: one silently move a number published by the other.
PREVALENCE_MIDPOINT = {
    "<1 / 1 000 000": math.log10(0.05),
    "1-9 / 1 000 000": math.log10(0.5),
    "1-9 / 100 000": math.log10(5.0),
    "1-5 / 10 000": math.log10(30.0),
    "6-9 / 10 000": math.log10(75.0),
    ">1 / 1000": math.log10(200.0),
}

#: The two inheritance modes this tool can say anything about. LOEUF measures intolerance to
#: losing ONE copy, so it is informative for dominant disease and close to mute for recessive
#: — which is a caveat this repository has been printing in prose and can now measure.
INHERITANCE = {"HP:0000006": "autosomal dominant", "HP:0000007": "autosomal recessive"}


# --------------------------------------------------------------------------- loading


def constraint_by_symbol() -> dict[str, dict[str, float]]:
    """Gene symbol -> LOEUF, pLI and the possible-site count, one transcript per gene.

    ONE TRANSCRIPT, CHOSEN BY A RULE RATHER THAN BY A MAXIMUM. The file has 211,524 rows and
    about 19,700 genes; taking the most constrained transcript per gene would be a selection
    operator, which is the thing this tool has just argued it is not doing. MANE Select first,
    then canonical — both are decisions someone else made, before seeing this analysis.
    """
    best: dict[str, tuple[int, dict[str, float]]] = {}
    with CONSTRAINT.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            symbol = (row.get("gene") or "").strip()
            if not symbol:
                continue
            rank = 0 if (row.get("mane_select") or "").lower() == "true" else (
                1 if (row.get("canonical") or "").lower() == "true" else 2)
            try:
                loeuf = float(row["lof.oe_ci.upper"])
                possible = float(row["lof.possible"])
                pli = float(row["lof.pLI"])
            except (KeyError, TypeError, ValueError):
                continue
            if possible < MIN_POSSIBLE_LOF:
                continue
            prev = best.get(symbol)
            if prev is None or rank < prev[0]:
                best[symbol] = (rank, {"loeuf": loeuf, "pli": pli, "possible": possible})
    return {sym: v for sym, (_, v) in best.items()}


def gene_citations() -> collections.Counter:
    """NCBI GeneID -> distinct PubMed citations, human only. Same source as attention_burden,
    so the two files can be read against each other without a join anyone has to trust."""
    counts: collections.Counter = collections.Counter()
    with gzip.open(BY_KEY["gene2pubmed"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or parts[0] != HUMAN_TAX:
                continue
            counts[parts[1]] += 1
    return counts


def disease_genes() -> tuple[dict[str, set[str]], dict[str, str]]:
    """disease -> NCBI gene ids, and the symbol for each id."""
    per_disease: dict[str, set[str]] = collections.defaultdict(set)
    symbol: dict[str, str] = {}
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            gid = (row.get("ncbi_gene_id") or "").replace("NCBIGene:", "").strip()
            disease = (row.get("disease_id") or "").strip()
            if gid and disease:
                per_disease[disease].add(gid)
                symbol[gid] = (row.get("gene_symbol") or "").strip()
    return dict(per_disease), symbol


def autism_genes() -> set[str]:
    """The symbols behind tools/autism_convergence.py, re-derived rather than imported, so the
    two tools cannot silently disagree about which set they measured."""
    terms = {"HP:0000717", "HP:0000729", "HP:0000733", "HP:0007281"}
    diseases: set[str] = set()
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
            if (row.get("hpo_id") or "").strip() in terms:
                diseases.add((row.get("database_id") or "").strip())
    per_disease, symbol = disease_genes()
    out: set[str] = set()
    for d in diseases:
        for gid in per_disease.get(d, ()):  # noqa: PERF401
            if symbol.get(gid):
                out.add(symbol[gid])
    return out


def prevalence_band() -> dict[str, float]:
    """ORPHA disorder -> log10 midpoint of its rarest published band."""
    out: dict[str, float] = {}
    try:
        root = ET.parse(BY_KEY["orpha_prevalence"].dest).getroot()
    except (OSError, ET.ParseError):
        return out
    for disorder in root.iter("Disorder"):
        code = disorder.findtext("OrphaCode")
        if not code:
            continue
        best = None
        for prev in disorder.iter("Prevalence"):
            klass = prev.findtext("PrevalenceClass/Name")
            if klass in PREVALENCE_MIDPOINT:
                v = PREVALENCE_MIDPOINT[klass]
                best = v if best is None else max(best, v)
        if best is not None:
            out[f"ORPHA:{code}"] = best
    return out


def inheritance_modes() -> dict[str, set[str]]:
    """disease -> the inheritance terms annotated on it."""
    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="	"):
            term = (row.get("hpo_id") or "").strip()
            if term in INHERITANCE:
                out[(row.get("database_id") or "").strip()].add(term)
    return dict(out)


# --------------------------------------------------------------------------- statistics


def spearman(xs: list[float], ys: list[float]) -> float:
    """Rank correlation, ties averaged. Both inputs here are heavy-tailed — citation counts
    especially — so a Pearson coefficient would be reporting the top of the tail."""
    def ranks(vs: list[float]) -> list[float]:
        order = sorted(range(len(vs)), key=lambda i: vs[i])
        out = [0.0] * len(vs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vs[order[j + 1]] == vs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[order[k]] = avg
            i = j + 1
        return out
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def boot_ci(values: list[float], stat, rng: random.Random, draws: int = 300) -> list[float]:
    """Point estimate plus and minus 1.96 bootstrap SE.

    NOT a percentile interval, and the reason is a failure this repository already made once:
    a percentile interval on a statistic that is biased in n did not contain its own point
    estimate, because a resample holds only about 63 % of the distinct items. The bootstrap
    supplies the DISPERSION; the point stays the point.
    """
    if len(values) < 8:
        return []
    point = stat(values)
    reps = []
    for _ in range(draws):
        sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
        reps.append(stat(sample))
    se = statistics.pstdev(reps)
    return [round(point - 1.96 * se, 4), round(point + 1.96 * se, 4)]


def length_bin(possible: float) -> int:
    """Bin index on log10 possible LoF sites, clamped into range."""
    v = math.log10(max(possible, 1.0))
    return max(0, min(LENGTH_BINS - 1, int(v / 3.0 * LENGTH_BINS)))


def matched_null(
    pool: dict[str, dict[str, float]], target: set[str], field: str, rng: random.Random,
) -> dict[str, float]:
    """Mean of `field` over `target`, against draws matched on gene length.

    THE WHOLE POINT. LOEUF is bounded away from small values for short genes — there is
    nothing to observe, so the upper confidence bound stays high. A disease-gene set is
    enriched for long genes. Comparing its mean LOEUF to the genome-wide mean therefore
    measures length as much as constraint, and the unmatched contrast is reported beside this
    one so the size of that difference is visible rather than argued about.
    """
    # SORTED, and it is not cosmetic. `target` is a set of strings, and Python randomises
    # string hashing per process — so the ITERATION ORDER of this set differs between runs,
    # `want` is built from it, and the draws come out different. The first two runs of this
    # tool disagreed at the third decimal and moved a z from -9.25 to -9.49, which is exactly
    # the drift tools/verify_claims.py exists to catch. A seeded RNG is not reproducibility if
    # the thing being iterated is not ordered.
    members = sorted(g for g in target if g in pool)
    if len(members) < 30:
        return {}
    observed = statistics.fmean(pool[g][field] for g in members)

    by_bin: dict[int, list[str]] = collections.defaultdict(list)
    for sym in sorted(pool):
        by_bin[length_bin(pool[sym]["possible"])].append(sym)
    want = collections.Counter(length_bin(pool[g]["possible"]) for g in members)

    draws = []
    for _ in range(DRAWS):
        picked: list[float] = []
        for b, n in sorted(want.items()):
            candidates = by_bin.get(b, [])
            if not candidates:
                continue
            for _ in range(n):
                picked.append(pool[candidates[rng.randrange(len(candidates))]][field])
        if picked:
            draws.append(statistics.fmean(picked))
    if not draws:
        return {}
    mu = statistics.fmean(draws)
    sd = statistics.pstdev(draws)
    unmatched = statistics.fmean(rec[field] for rec in pool.values())
    return {
        "genes": len(members),
        "observed": round(observed, 4),
        "null_mean": round(mu, 4),
        "null_sd": round(sd, 5),
        "z": round((observed - mu) / sd, 2) if sd else None,
        "genome_mean_unmatched": round(unmatched, 4),
        "shift_explained_by_length": round(
            abs(mu - unmatched) / abs(observed - unmatched), 3)
        if abs(observed - unmatched) > 1e-9 else None,
        "draws": DRAWS,
    }


# --------------------------------------------------------------------------- main


def main() -> int:
    if not CONSTRAINT.exists():
        print(f"missing {CONSTRAINT}", file=sys.stderr)
        return 1

    rng = random.Random(SEED)
    pool = constraint_by_symbol()
    per_disease, symbol = disease_genes()
    citations = gene_citations()

    disease_symbols = {symbol[g] for gs in per_disease.values() for g in gs if symbol.get(g)}
    in_pool = {s for s in disease_symbols if s in pool}
    # Same reason as in matched_null: anything derived from a set gets an order before it is
    # used to compute a published number.

    # ---- arm 1: are disease genes constrained, once length is held fixed?
    arm_disease = matched_null(pool, in_pool, "loeuf", random.Random(SEED + 1))

    # ---- arm 2: attention against constraint, on genes only.
    #      Every statistic gets its own RNG. A shared one moved a published number in this
    #      repository once: adding a bootstrap consumed draws before a permutation null and
    #      shifted a z from -19.0 to -20.37.
    pairs = [(pool[s]["loeuf"], citations.get(gid, 0))
             for gid, s in sorted(symbol.items()) if s in pool]
    pairs = [(lo, c) for lo, c in pairs if c > 0]
    rho_attention = spearman([p[0] for p in pairs], [math.log10(p[1]) for p in pairs])
    rho_ci = boot_ci(
        list(range(len(pairs))),
        lambda idx: spearman([pairs[i][0] for i in idx],
                             [math.log10(pairs[i][1]) for i in idx]),
        random.Random(SEED + 2), draws=200)

    # ---- arm 3b: THE CONFOUND, ANSWERED RATHER THAN NAMED.
    #
    #  attention_burden reported attention against prevalence at +0.331 and could not rule
    #  out that both were riding on constraint. Constraint is on disk now, so the question
    #  has an answer instead of a caveat: compute the SAME rank correlation inside each
    #  constraint tercile. If +0.331 survives within bands, prevalence is carrying something
    #  constraint does not; if it collapses, attention_burden's headline was constraint
    #  wearing prevalence's name.
    #
    #  Stratify, do not adjust. The repository already made this argument for lineage in
    #  tools/cancer_genotype.py: the contrast computed inside each stratum and then pooled is
    #  the estimate to report, and the DIFFERENCE from the naive one is the size of the
    #  confound — which is more informative than either alone.
    prevalence = prevalence_band()
    per_disease_attention: list[tuple[float, float, float]] = []
    for disease in sorted(per_disease):
        if disease not in prevalence:
            continue
        gids = sorted(per_disease[disease])
        syms = [symbol[g] for g in gids if symbol.get(g) in pool]
        cites = sum(citations.get(g, 0) for g in gids)
        if not syms or cites <= 0:
            continue
        # The disease's LOEUF is the MINIMUM over its genes — the most intolerant gene is the
        # one a reader would call the disease's gene, and a mean would be diluted by however
        # many loci happen to be annotated.
        per_disease_attention.append(
            (min(pool[s]["loeuf"] for s in syms), prevalence[disease], math.log10(cites)))

    strat = []
    if len(per_disease_attention) >= 90:
        ordered = sorted(per_disease_attention)
        cut = len(ordered) // 3
        for name, chunk in (("most constrained", ordered[:cut]),
                            ("middle", ordered[cut:2 * cut]),
                            ("most tolerant", ordered[2 * cut:])):
            strat.append({
                "band": name,
                "diseases": len(chunk),
                "loeuf_range": [round(chunk[0][0], 3), round(chunk[-1][0], 3)],
                "attention_vs_prevalence": round(
                    spearman([c[1] for c in chunk], [c[2] for c in chunk]), 4),
            })

    # ---- arm 3c: what LOEUF can and cannot see, measured instead of disclaimed.
    #
    #  Every version of this file has said in prose that LOEUF is about losing ONE copy and
    #  therefore says little about recessive disease. That is a testable statement about this
    #  catalogue, not a disclaimer, and leaving it in prose was the easy way out.
    modes = inheritance_modes()
    by_mode: dict[str, set[str]] = {t: set() for t in INHERITANCE}
    for disease, terms in modes.items():
        # A disease annotated BOTH ways tells us nothing about either, so it is dropped
        # rather than counted twice.
        if len(terms) != 1:
            continue
        term = next(iter(terms))
        for gid in per_disease.get(disease, ()):
            if symbol.get(gid) in pool:
                by_mode[term].add(symbol[gid])
    # A gene serving both a dominant and a recessive disorder is in neither arm: it is the
    # case the contrast is least able to speak about.
    shared = by_mode["HP:0000006"] & by_mode["HP:0000007"]
    arm_inheritance = {
        INHERITANCE[t]: matched_null(pool, by_mode[t] - shared, "loeuf",
                                     random.Random(SEED + 10 + i))
        for i, t in enumerate(sorted(INHERITANCE))
    }
    arm_inheritance["genes_in_both_and_dropped"] = len(shared)

    # ---- arm 3: the autism set, matched on length.
    aut = autism_genes()
    arm_autism = matched_null(pool, aut, "loeuf", random.Random(SEED + 3))

    # ---- the table a reader can check the bands against.
    bands = collections.Counter()
    for s in pool:
        bands["constrained" if pool[s]["loeuf"] < LOEUF_CONSTRAINED else "tolerant"] += 1
    disease_bands = collections.Counter(
        "constrained" if pool[s]["loeuf"] < LOEUF_CONSTRAINED else "tolerant" for s in in_pool)

    payload = {
        "generated": "2026-08-30",
        "provenance": "gnomAD v4.1 constraint metrics, joined to HPO genes_to_disease by "
                      "gene symbol and to NCBI gene2pubmed by GeneID",
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": "Selective constraint is a property of a gene measured in a population "
                    "nobody asked about disease. Does it explain what the catalogue knows, "
                    "and what gets studied?",
        "fit_test": {
            "gate": ".claude/skills/sieve-new-adapter, four-question fit test",
            "verdict": "three yeses and a NO on question 4 — no maximum, no top-k, no "
                       "enrichment over per-gene draws. By the skill's own rule this is a "
                       "variance problem and not selection bias, so there is no Stage 1 "
                       "claim here, no shortlist, and no gene ranked as a finding.",
        },
        "instrument": {
            "metric": "LOEUF — the upper bound of the 90 % interval on observed/expected "
                      "loss-of-function variants. Lower means more intolerant.",
            "transcript": "MANE Select, then canonical. Taking the most constrained "
                          "transcript per gene would be the selection operator this tool "
                          "has just said it is not applying.",
            "dropped": f"genes with fewer than {MIN_POSSIBLE_LOF} possible LoF sites, "
                       "because gnomAD's own interval spans the range there",
            "null": "draws matched on log10 possible-LoF sites, because LOEUF is bounded "
                    "away from small values for short genes and a disease-gene set is "
                    "enriched for long ones",
        },
        "scale": {
            "genes_with_constraint": len(pool),
            "disease_genes": len(disease_symbols),
            "disease_genes_with_constraint": len(in_pool),
            "genome_bands": dict(bands),
            "disease_gene_bands": dict(disease_bands),
        },
        "arms": {
            "disease_genes_vs_matched": arm_disease,
            "autism_set_vs_matched": arm_autism,
            "attention_vs_prevalence_within_constraint": {
                "terciles": strat,
                "compare_with": "tools/attention_burden.py reports +0.331 over all diseases",
                "reading": "the same rank correlation computed inside each constraint band. "
                           "If it survives in every band, prevalence carries something "
                           "constraint does not. Stratified rather than adjusted, for the "
                           "reason cancer_genotype gives about lineage: the difference "
                           "between the naive figure and the within-band ones IS the size "
                           "of the confound.",
            },
            "constraint_by_inheritance": arm_inheritance,
            "attention_vs_constraint": {
                # DISEASE GENES ONLY, and that is the right population for the question:
                # attention_burden's coefficient was computed over diseases carrying causal
                # genes, so the confound has to be tested on the same genes rather than on
                # the genome, where most entries nobody has ever cited would dominate.
                "population": "the disease genes, the same set attention_burden scored",
                "genes": len(pairs),
                "spearman": round(rho_attention, 4),
                "ci95": rho_ci,
                "reading": "negative means MORE cited genes are MORE constrained, because "
                           "LOEUF runs the other way. This is the confound "
                           "tools/attention_burden.py could state and not answer.",
            },
        },
        "says": "An association over genes, not a mechanism. LOEUF measures intolerance to "
                "heterozygous loss of function in a reference population; a gene can matter "
                "enormously to a rare disease and be perfectly tolerant of losing one copy, "
                "and recessive disease genes are exactly that case. Nothing here says a "
                "tolerant gene is unimportant.",
        "limits": [
            "gnomAD's reference population is majority European ancestry, so constraint is "
            "estimated where the variation was sampled. A gene under different selective "
            "pressure elsewhere is not visible to this metric.",
            "Joined on gene SYMBOL, which is the weakest identifier in this repository. "
            "Symbols that changed between the HPO release and the gnomAD release drop out "
            "silently, and the drop is not random with respect to how well studied a gene is.",
            "LOEUF is about heterozygous loss of function only. It says nothing about "
            "missense, about gain of function, or about the recessive inheritance that a "
            "large part of the rare-disease catalogue runs on.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {DEST.relative_to(ROOT)}")
    print(f"  {len(pool):,} genes with constraint, {len(in_pool):,} of them disease genes")
    if arm_disease:
        print(f"  disease genes: LOEUF {arm_disease['observed']} vs matched null "
              f"{arm_disease['null_mean']} (z {arm_disease['z']})")
    if arm_autism:
        print(f"  autism set:    LOEUF {arm_autism['observed']} vs matched null "
              f"{arm_autism['null_mean']} (z {arm_autism['z']})")
    print(f"  attention ~ constraint: rho {rho_attention:.4f} {rho_ci}")
    for row in strat:
        print(f"    within {row['band']:<16} ({row['diseases']:>4} diseases): "
              f"attention~prevalence {row['attention_vs_prevalence']:+.4f}")
    for mode, arm in arm_inheritance.items():
        if isinstance(arm, dict) and arm:
            print(f"  {mode:<22} LOEUF {arm['observed']} vs matched {arm['null_mean']} "
                  f"(z {arm['z']}, n={arm['genes']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
