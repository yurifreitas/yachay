# The target model — what a gene's own evidence admits, and what it does not

> **Role:** how to use `sieve.stages.target` and the `sieve target` command to assess a gene
> as a gene-editing target in rare disease. This is the one part of the project meant to be
> **run by other people on their own data**, so it is a how-to, not an argument.
> **Last revised:** 2026-08-28 · **State:** implemented and tested (19 tests). Two axes —
> quantified endpoint and DepMap dependency share — are wired but sparsely populated; the
> model reports them as unmeasured rather than defaulting them, which is the point.
>
> The argument for the design is in the module docstring of
> [`../../src/sieve/stages/target.py`](../../src/sieve/stages/target.py). The backlog is in
> [`../roadmap.md`](../roadmap.md).

---

## It does not produce a score, and that is the design

Every comparable tool emits a ranking: a druggability score, a tractability index, a
composite of normalised axes. This emits none.

`out/rare/dossiers.json` has carried the reason in its own caveat since long before this
stage existed — *"No severity score, no burden index, no composite. Those need value
judgements this file has no basis for."* A target score is that object under a different
name. Weighting allelic recurrence against VUS burden against pan-essentiality means
deciding **how many uncertain variants are worth one recurrent allele**, and nobody has that
exchange rate.

What the evidence *can* say is narrower and more useful:

- **which editing strategies this gene's variant spectrum admits**, and
- **which gate it fails.**

A reader who disagrees with a gate can move it — every threshold is an argument to
`assess()`, not a constant buried in a branch. A reader who disagrees with a weight inside a
composite cannot even see it.

---

## Using it

```bash
sieve stages                      # which of the ten stages are implemented
sieve target LMNA NF1 STXBP1      # assess named genes
sieve target --top 20             # the genes with the most patients on file
sieve target --json LMNA          # machine-readable, for a pipeline
```

From Python, with your own numbers rather than ours:

```python
import sieve as sv

a = sv.assess(
    "NF1",
    patients=405, distinct_variants=42, private_share=0.43, most_recurrent=107,
    consequences={"missense": 369, "frameshift": 15, "nonsense": 21},
    vus_share=0.31, pan_essential=False, quantified_signs=4,
)
a.admitted        # ['allele-specific editing', 'base editing', 'knockdown or knockout']
a.failed_gates    # the gates that did not pass, each with a reason
a.unknown_axes    # what was never measured — blocking, not zero
```

**Every argument is optional and `None` means *not measured*, never zero.** An unmeasured
axis blocks the strategies that depend on it. That is the contract the tests spend most of
their assertions on: a gene with no essentiality data must not come back as knockable.

---

## The five strategies, and what rules each one out

| strategy | admitted when | ruled out by |
|---|---|---|
| **allele-specific editing** | one allele is carried by ≥ 10 patients | a spectrum where every variant is private |
| **base editing** | substitutions dominate the spectrum | an indel- or deletion-dominated spectrum |
| **exon skipping** | ≥ 30 % of variants truncate | a missense-dominated spectrum |
| **gene replacement** | loss of function dominates | a gain-of-function mechanism |
| **knockdown / knockout** | the gene is not pan-essential | **pan-essentiality** — the one hard veto |

The mapping is mechanistic rather than statistical, and it is the part a domain expert
should argue with first. The thresholds in the table are the defaults; all four are
arguments.

---

## The four gates

A gate is a stage of [`../methodology.md`](../methodology.md) asked of a target. **Failing a
gate does not mean the gene is a bad target** — it means the evidence to nominate it is not
there yet, which is a different and more actionable statement.

| stage | gate | asks |
|---|---|---|
| 2 | Power | is there a quantified endpoint to power a trial on? |
| 3 | Confound | is the dependency selective, or pan-essential toxicity? |
| 6 | Prior | is a new patient's variant likely to be interpretable at all? |
| 7 | Shortlist | are the nominated targets spread across mechanisms? |

The last is a property of a **set**, not of a gene, which is why `shortlist()` exists beside
`assess()` — and why it **refuses to claim diversification when no module map is supplied**:

```
No module map was supplied, so Stage 7 diversification COULD NOT BE CHECKED. This
shortlist may be one hypothesis with several gene names.
```

That refusal is live today. Reactome is ingested and unread ([`../roadmap.md`](../roadmap.md)
1.1), so the module map does not exist yet — and returning a shortlist that merely *looked*
diversified would be the exact failure Stage 7 is named for.

---

## What it reads, and what is thin

| axis | from | state |
|---|---|---|
| allelic spectrum, consequence mix | `tools/patient_variants.py` | **699 genes** |
| VUS share | `tools/clinvar_evidence.py` | **13,528 genes** |
| pan-essentiality | the DepMap adapter's `is_common_essential` | 17,916 genes |
| quantified endpoint | `tools/evidence_atlas.py` | ⚠ **not yet wired per gene** — the atlas is per organ system |
| dependency share | the DepMap adapter | ⚠ available, not yet joined |

The two marked axes are why most assessments currently print `unmeasured: dependentLineShare,
quantifiedSigns` and fail the Power gate. **That is the honest state, not a bug**: the model
is reporting that the evidence to clear those gates has not been assembled, which is exactly
what it exists to do.

---

## A worked example, and its limits

```
  NF1
    405 patients · 42 variants · 43% private · top allele 107
    YES  allele-specific editing    one allele is carried by 107 patients …
    YES  base editing               substitutions dominate the spectrum (369 of 405)
     no  exon skipping              only 15 of 405 variants truncate …
     no  gene replacement           the spectrum is not loss-of-function dominated …
    YES  knockdown or knockout      not in the DepMap common-essential set …
    GATE  Stage 2 Power: no sign of this gene's disease has a real denominator
```

**Read the counts carefully.** `405` is variant *records* — one per patient carrying the
variant — while `42` is distinct alleles. The consequence mix is weighted by patients on
purpose: what an editing strategy has to address is people, not alleles.

**And the standing caveat on everything upstream.** The patient corpus is published, solved
cases: all 11,243 of its ACMG classifications are `PATHOGENIC`, and ClinVar disagrees with
about a fifth of them ([`patient-data.md`](patient-data.md) §2e, [`../audit.md`](../audit.md)
A21). The model measures the **record**. Nothing here is a claim about a patient who has not
been written up.
