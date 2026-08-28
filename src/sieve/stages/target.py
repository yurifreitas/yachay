"""Stage 7 — Shortlist, applied to gene-editing targets in rare disease.

The idea in one sentence: **before nominating a gene as an editing target, say which
approach its own evidence admits, and which gate it fails.**

## Why this is not a score

Everything else in this space produces a ranking: a druggability score, a tractability
index, a composite of five normalised axes. This produces none, and the refusal is the
design. `out/rare/dossiers.json` already carries the reason in its own caveat —

    "No severity score, no burden index, no composite. Those need value judgements this
     file has no basis for."

— and a target score is the same object with a different name. Weighting allelic
recurrence against VUS burden against pan-essentiality means deciding how many uncertain
variants are worth one recurrent allele, and nobody has that exchange rate. What the
evidence *can* say is narrower and more useful: **which editing strategies this gene's
variant spectrum admits, and which gates it fails.** A reader who disagrees with a gate can
move it; a reader who disagrees with a weight inside a composite cannot even see it.

## The axes, and where each comes from

Every one is measured elsewhere in this project and read here. Nothing is invented.

    allelic spectrum    tools/patient_variants.py   distinct variants, private share,
                                                    most recurrent allele
    consequence mix     tools/patient_variants.py   loss of function against missense
    interpretability    tools/clinvar_evidence.py   the gene's VUS share
    essentiality        the DepMap adapter          is knocking it down toxic?
    phenotype evidence  tools/evidence_atlas.py     is there a quantified endpoint at all?

## The strategies, and what rules each one out

The mapping is mechanistic, not statistical, and it is the part a domain expert should argue
with first:

| strategy | needs | ruled out by |
|---|---|---|
| allele-specific editing | a recurrent allele carried by many patients | a spectrum where every variant is private |
| base editing | point substitutions dominating the spectrum | indel- or deletion-dominated spectra |
| exon skipping | frameshift or nonsense variants in a skippable frame | missense-dominated spectra |
| gene replacement | loss of function, and a codable transcript | gain-of-function mechanisms, oversized transcripts |
| knockdown / knockout | a gain-of-function or dominant-negative mechanism | **pan-essentiality** — the gene is needed by every cell |

## The gates

A gate is a stage of `docs/methodology.md` asked of a target. Failing one does not mean the
gene is a bad target; it means the evidence to nominate it is not there yet, which is a
different and more actionable statement.

    Stage 2  Power        is there a quantified endpoint to power a trial on?
    Stage 3  Confound     is the dependency selective, or is it pan-essential toxicity?
    Stage 6  Prior        is the mechanism known well enough to pick a direction?
    Stage 7  Shortlist    are the nominated targets spread across mechanisms, or is this
                          one hypothesis wearing several gene names?

The last one is a property of a *set*, not of a gene, which is why `shortlist()` exists
beside `assess()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

# ---------------------------------------------------------------------------------------
# Thresholds. Every one is a judgement, so every one is a named module constant with a
# comment rather than a number buried in a branch - and `assess()` takes them as arguments
# so a caller who disagrees can move them without editing the library.
# ---------------------------------------------------------------------------------------

#: A variant carried by at least this many patients is worth designing a specific edit for.
#: Below it, an allele-specific approach serves too few people to justify its development.
RECURRENT_ALLELE_PATIENTS = 10

#: Above this share of private (seen-once) variants, the spectrum is effectively per-family
#: and a per-variant strategy stops scaling.
PRIVATE_SPECTRUM = 0.80

#: Above this share of variants of uncertain significance, a new patient's variant is more
#: likely than not to be uninterpretable - which is an eligibility problem before it is a
#: therapeutic one.
UNINTERPRETABLE_VUS = 0.60

#: A gene depended on by at least this share of screened lines is treated as pan-essential:
#: knocking it down is toxicity, not therapy. The DepMap convention.
PAN_ESSENTIAL_LINES = 0.90


@dataclass(frozen=True)
class Evidence:
    """One measured property of a gene, with where it came from and what is missing."""

    name: str
    value: object
    source: str
    #: `None` means the axis was not measurable for this gene - never assume a default.
    known: bool = True

    def __str__(self) -> str:
        return f"{self.name}={self.value!r}" if self.known else f"{self.name}=unknown"


@dataclass(frozen=True)
class Strategy:
    name: str
    admitted: bool
    because: str


@dataclass(frozen=True)
class Gate:
    stage: int
    name: str
    passed: bool
    because: str


@dataclass
class Assessment:
    """What one gene's evidence admits. Deliberately not a score."""

    gene: str
    evidence: list[Evidence] = field(default_factory=list)
    strategies: list[Strategy] = field(default_factory=list)
    gates: list[Gate] = field(default_factory=list)

    @property
    def admitted(self) -> list[str]:
        return [s.name for s in self.strategies if s.admitted]

    @property
    def failed_gates(self) -> list[Gate]:
        return [g for g in self.gates if not g.passed]

    @property
    def unknown_axes(self) -> list[str]:
        return [e.name for e in self.evidence if not e.known]

    def summary(self) -> str:
        if not self.admitted:
            return f"{self.gene}: no strategy admitted by the evidence on file"
        gates = (f"; fails {', '.join(g.name for g in self.failed_gates)}"
                 if self.failed_gates else "")
        return f"{self.gene}: {', '.join(self.admitted)}{gates}"


def assess(
    gene: str,
    *,
    patients: int | None = None,
    distinct_variants: int | None = None,
    private_share: float | None = None,
    most_recurrent: int | None = None,
    consequences: dict[str, int] | None = None,
    vus_share: float | None = None,
    dependent_line_share: float | None = None,
    pan_essential: bool | None = None,
    quantified_signs: int | None = None,
    recurrent_allele_patients: int = RECURRENT_ALLELE_PATIENTS,
    private_spectrum: float = PRIVATE_SPECTRUM,
    uninterpretable_vus: float = UNINTERPRETABLE_VUS,
    pan_essential_lines: float = PAN_ESSENTIAL_LINES,
) -> Assessment:
    """Assess one gene as an editing target from evidence measured elsewhere.

    Every argument is optional and `None` means **not measured**, never zero. An axis that
    was not measured produces `known=False` evidence and blocks the strategies that depend
    on it, rather than letting a missing input read as a negative one — which is the same
    modelling decision `references/rare-disease-lexicon.md` makes about the unknown.

    >>> a = assess("LMNA", patients=259, distinct_variants=55, private_share=0.545,
    ...            most_recurrent=62, consequences={"missense": 200, "nonsense": 14},
    ...            vus_share=0.42)
    >>> "allele-specific editing" in a.admitted
    True
    """
    ev: list[Evidence] = []
    strategies: list[Strategy] = []
    gates: list[Gate] = []

    def add(name, value, source):
        ev.append(Evidence(name, value, source, known=value is not None))

    add("patients", patients, "tools/patient_variants.py")
    add("distinctVariants", distinct_variants, "tools/patient_variants.py")
    add("privateShare", private_share, "tools/patient_variants.py")
    add("mostRecurrentAllele", most_recurrent, "tools/patient_variants.py")
    add("consequences", consequences, "tools/patient_variants.py")
    add("vusShare", vus_share, "tools/clinvar_evidence.py")
    add("dependentLineShare", dependent_line_share, "the DepMap adapter")
    add("panEssential", pan_essential, "the DepMap adapter (AchillesCommonEssentialControls)")
    add("quantifiedSigns", quantified_signs, "tools/evidence_atlas.py")

    cons = consequences or {}
    total_cons = sum(cons.values()) or None
    lof = (cons.get("nonsense", 0) + cons.get("frameshift", 0))
    missense = cons.get("missense", 0)
    indel = (cons.get("deletion", 0) + cons.get("insertion", 0)
             + cons.get("duplication", 0) + cons.get("indel", 0))

    # ---- strategies -------------------------------------------------------------------
    if most_recurrent is None:
        strategies.append(Strategy(
            "allele-specific editing", False,
            "the allelic spectrum was not measured, so recurrence is unknown"))
    elif most_recurrent >= recurrent_allele_patients:
        strategies.append(Strategy(
            "allele-specific editing", True,
            f"one allele is carried by {most_recurrent} patients, at or above the "
            f"threshold of {recurrent_allele_patients}"))
    else:
        strategies.append(Strategy(
            "allele-specific editing", False,
            f"the most recurrent allele reaches only {most_recurrent} patients"))

    if total_cons is None:
        strategies.append(Strategy("base editing", False,
                                   "the consequence mix was not measured"))
    elif indel / total_cons > 0.5:
        strategies.append(Strategy(
            "base editing", False,
            f"the spectrum is indel-dominated ({indel} of {total_cons}); base editors "
            "change single bases"))
    else:
        strategies.append(Strategy(
            "base editing", True,
            f"substitutions dominate the spectrum ({total_cons - indel} of {total_cons})"))

    if total_cons is None:
        strategies.append(Strategy("exon skipping", False,
                                   "the consequence mix was not measured"))
    elif lof / total_cons >= 0.3:
        strategies.append(Strategy(
            "exon skipping", True,
            f"{lof} of {total_cons} variants truncate, which is what skipping addresses"))
    else:
        strategies.append(Strategy(
            "exon skipping", False,
            f"only {lof} of {total_cons} variants truncate; skipping does not help a "
            "missense-dominated spectrum"))

    if private_share is None:
        strategies.append(Strategy("gene replacement", False,
                                   "the allelic spectrum was not measured"))
    elif total_cons and lof / total_cons >= 0.3:
        strategies.append(Strategy(
            "gene replacement", True,
            f"loss of function accounts for {lof} of {total_cons} variants, and replacement "
            f"is variant-agnostic — which is what a {private_share:.0%} private spectrum "
            "needs"))
    else:
        strategies.append(Strategy(
            "gene replacement", False,
            "the spectrum is not loss-of-function dominated, so replacing the gene may not "
            "address the mechanism"))

    # The DepMap adapter publishes a MEASURED flag, `is_common_essential`, taken from the
    # Achilles control set. Preferring it over a threshold on a fraction we would have to
    # derive is the same discipline as reading the lexicon's own band table rather than
    # authoring one (docs/audit.md A13).
    if pan_essential is True:
        strategies.append(Strategy(
            "knockdown or knockout", False,
            "pan-essential in DepMap: every screened lineage depends on it, so knocking it "
            "down is toxicity rather than therapy"))
    elif pan_essential is False and dependent_line_share is None:
        strategies.append(Strategy(
            "knockdown or knockout", True,
            "not in the DepMap common-essential set, so loss is tolerated outside the "
            "disease context"))
    elif dependent_line_share is None:
        strategies.append(Strategy(
            "knockdown or knockout", False,
            "essentiality was not measured, and knocking down a gene without knowing "
            "whether every cell needs it is the failure Stage 3 exists to prevent"))
    elif dependent_line_share >= pan_essential_lines:
        strategies.append(Strategy(
            "knockdown or knockout", False,
            f"pan-essential: {dependent_line_share:.0%} of screened lines depend on it, so "
            "knocking it down is toxicity rather than therapy"))
    else:
        strategies.append(Strategy(
            "knockdown or knockout", True,
            f"only {dependent_line_share:.0%} of lines depend on it, so loss is tolerated "
            "outside the disease context"))

    # ---- gates ------------------------------------------------------------------------
    gates.append(Gate(
        2, "Power",
        bool(quantified_signs),
        (f"{quantified_signs} signs of this gene's disease are estimated from a real series"
         if quantified_signs else
         "no sign of this gene's disease has a real denominator, so there is no quantified "
         "endpoint to power a trial on")))

    if pan_essential is not None:
        gates.append(Gate(
            3, "Confound", not pan_essential,
            ("pan-essential in DepMap — a dependency here is toxicity, not selectivity"
             if pan_essential else "not pan-essential in DepMap")))
    else:
        gates.append(Gate(
            3, "Confound",
            dependent_line_share is not None and dependent_line_share < pan_essential_lines,
            ("essentiality is unmeasured" if dependent_line_share is None else
             f"{dependent_line_share:.0%} of lines depend on it")))

    gates.append(Gate(
        6, "Prior",
        vus_share is not None and vus_share < uninterpretable_vus,
        ("the gene's interpretability was not measured" if vus_share is None else
         f"{vus_share:.0%} of its ClinVar variants are of uncertain significance — above "
         f"{uninterpretable_vus:.0%} a new patient is more likely than not to be "
         "uninterpretable, which is an eligibility problem before a therapeutic one"
         if vus_share >= uninterpretable_vus else
         f"{vus_share:.0%} of its ClinVar variants are uncertain")))

    return Assessment(gene=gene, evidence=ev, strategies=strategies, gates=gates)


def shortlist(
    assessments: Iterable[Assessment],
    *,
    modules: dict[str, str] | None = None,
    slots: int = 10,
) -> dict:
    """Stage 7 proper: a set property, not a gene property.

    The stage exists to stop a shortlist betting every slot on one point of failure.
    `references/rare-disease-mechanisms.md` §4 argues the unit of failure is the signalling
    MODULE, not the gene: ten genes from one module is one hypothesis with ten labels.

    `modules` maps gene to module. **If it is not supplied the diversification cannot be
    checked, and this function says so rather than returning a shortlist that looks
    diversified.** Reactome is ingested and unread (`docs/roadmap.md` 1.1), which is exactly
    why this argument exists and is currently empty.
    """
    picked = [a for a in assessments if a.admitted and not a.failed_gates][:slots]
    out = {
        "slots": slots,
        "eligible": len(picked),
        "genes": [a.gene for a in picked],
    }
    if not modules:
        out["diversified"] = None
        out["says"] = (
            "No module map was supplied, so Stage 7 diversification COULD NOT BE CHECKED. "
            "This shortlist may be one hypothesis with several gene names. Supply `modules` "
            "— see docs/roadmap.md 1.1."
        )
        return out

    by_module: dict[str, list[str]] = {}
    for a in picked:
        by_module.setdefault(modules.get(a.gene, "unmapped"), []).append(a.gene)
    biggest = max((len(v) for v in by_module.values()), default=0)
    out["byModule"] = by_module
    out["diversified"] = biggest <= max(2, slots // 3)
    out["says"] = (
        f"{len(by_module)} modules across {len(picked)} genes; the largest holds {biggest}."
        + ("" if out["diversified"] else
           " That is a concentrated shortlist: if the module is wrong, every slot in it "
           "fails together.")
    )
    return out
