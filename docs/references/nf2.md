# NF2 — neurofibromatosis type 2 / NF2-related schwannomatosis

> **Role:** the domain layer for the NF2 work — what a `sieve` shortlist for NF2 must know
> before it can be defended, plus the lexicon that makes the literature findable and the gene
> sets that make the analysis checkable.
> **Last revised:** 2026-08-26 · **State:** written from working knowledge; §8 lists the
> sources still to be attached. Genealogy in [`../lineage.md`](../lineage.md); citations in
> `CITATION.cff`.
>
> This is technical reference for prioritising research targets, **not clinical guidance**.
>
> Verification status: the biology and pathway claims below are settled and safe to build
> on. Specific trial names, release versions, and file names are the parts to check
> against a current source before they appear in a write-up. Nothing here is a clinical
> recommendation.

---

## 1. Naming — read this first

The disease and the gene no longer share a name, and mixing them up will corrupt any
literature search.

| term | what it means now |
|---|---|
| **NF2** (gene) | the tumour suppressor gene on chromosome 22q12, encoding merlin |
| **NF2-related schwannomatosis (NF2-SWN)** | the disease, renamed in the 2022 nomenclature update. Formerly "neurofibromatosis type 2" |
| **schwannomatosis** (`SMARCB1`-, `LZTR1`-related) | a *different* condition, previously "NF3". Not this |
| **NF1** | a different gene, a different chromosome (17q11), a different disease (neurofibromin, RAS-GAP). Not this |

Two consequences for the project:
- A query for "neurofibromatosis" returns mostly NF1 literature. Always qualify.
- The tumours in NF2-SWN are **schwannomas and meningiomas**, not neurofibromas. The
  eponym is actively misleading.

---

## 2. Gene and protein

- **Gene:** `NF2`, chromosome 22q12.2. Tumour suppressor; classic two-hit (Knudson)
  inactivation.
- **Protein:** **merlin** (moesin–ezrin–radixin-like protein), also called schwannomin.
  A FERM-domain protein linking the membrane and cortical actin cytoskeleton to
  growth-control signalling.
- **Loss mechanism:** both point mutation and **copy-number loss / chromosome 22
  deletion**. This matters practically — a subgroup defined only from a mutation table
  will miss a large fraction of NF2-null lines, so any analysis needs copy number too.
- **Somatic relevance beyond the germline disease:** `NF2` is somatically lost in a large
  share of **mesothelioma** and sporadic meningioma, and appears in renal and other
  cancers. This is why DepMap has enough NF2-null lines to analyse at all.

## 3. Pathway — why merlin loss matters

Merlin is an upstream activator of the **Hippo pathway**. Losing it releases the
transcriptional co-activators **YAP** and **TAZ** (`WWTR1`) to enter the nucleus and drive
growth programmes with the **TEAD** transcription factors.

    merlin (NF2)  ──▶  LATS1/2 kinases  ──▶  YAP / TAZ phosphorylated, held cytoplasmic
       ✗ lost              (inactive)              ▼
                                            YAP/TAZ nuclear ──▶ TEAD ──▶ proliferation

Other merlin-linked axes reported in the literature, weaker and less consistent than the
Hippo one: mTORC1 activation, receptor tyrosine kinase signalling (ErbB/PDGFR), FAK/Src,
and the CRL4-DCAF1 nuclear ubiquitin ligase.

**The consequence that makes NF2 tractable here:** merlin loss creates a *dependency*.
NF2-null cells lean on YAP/TAZ–TEAD in a way NF2-wildtype cells do not. That is a
genotype-defined synthetic-lethal contrast — exactly the shape a screen can rank.

## 4. Clinical picture (brief, for context only)

- Bilateral vestibular schwannomas are the hallmark; also meningiomas, spinal schwannomas,
  ependymomas, and juvenile cataract.
- The morbidity is hearing loss, balance failure, and cumulative surgical damage — not
  usually metastatic disease. **Tumours are benign and slow-growing.**
- Standard care is surgery and radiosurgery. Systemic options are limited; anti-VEGF
  (bevacizumab) is the most-used medical therapy for vestibular schwannoma, with hearing
  responses in a fraction of patients and no cure.
- Trials have targeted mTOR, ErbB, and more recently multi-RTK inhibition and TEAD
  inhibitors. TEAD inhibitors are the direct pharmacological expression of the Hippo logic
  above and are the most mechanistically motivated current class.

**Why this shapes the objective (Stage 0):** the endpoint that matters is *stopping growth
and preserving hearing in a benign tumour*, not maximal cytotoxicity. A target whose
knockout kills every cell line is worthless here for a stronger reason than usual — it
would be an unacceptable toxicity profile for a non-malignant, lifelong condition. The
DepMap adapter already scores selective dependency rather than raw killing; for NF2 that
choice is not a preference, it is the requirement.

## 5. The analysis this enables — NF2-null selective dependency in DepMap

This is the concrete, runnable NF2 application, and it uses data already partly on disk.

| | |
|---|---|
| entity | a gene (~18,000) |
| observation | one cell line's Chronos gene effect |
| aggregate | top-k dependency **within the NF2-null subgroup**, contrasted against NF2-wildtype lines |
| counts vary | **yes, and severely** — the NF2-null subgroup is small, and the number of lines screened differs per gene |

Where each stage bites:

- **Stage 0** — score selectivity, not killing (section 4). A pan-essential gene topping
  the list is the KIF11 lesson repeating.
- **Stage 1** — a top-k over a *small* subgroup is the most inflated case there is. With a
  handful of NF2-null lines, the expected maximum of pure noise is large. This is where
  the null model earns its place.
- **Stage 2** — power is the binding constraint. State the subgroup size up front; a
  contrast on a dozen lines supports far less than the ranking implies.
- **Stage 3** — confounds to regress out: lineage (mesothelioma is over-represented among
  NF2-null lines, so lineage-specific dependencies will masquerade as NF2 dependencies),
  screen quality, culture medium, growth rate, and chromosome-22 copy number generally.
  **The lineage confound is the main threat to this analysis.**
- **Stage 6** — the prior is unusually strong and unusually useful: `YAP1`, `WWTR1`,
  `TEAD1-4`, and `LATS1/2` behaviour is a **positive control**. If the calibrated ranking
  does not recover the Hippo axis, the pipeline is broken and no novel hit from it should
  be believed. That is a rare luxury — most `sieve` targets have no ground truth.
- **Stage 7** — a shortlist should not put every slot on the Hippo axis; that is the single
  point of failure this stage exists to prevent.

**The data blocker is closed.** `Model.csv` (lineage),
`OmicsSomaticMutationsMatrixDamaging.csv` (NF2 mutation calls) and `OmicsCNGene.csv` (NF2
deletion) were fetched on 2026-08-27 and the subgroup contrast runs; see
[`README.md`](README.md). All three were needed, because defining the NF2-null subgroup from
mutations alone would be wrong — deletion is a major loss mechanism (section 2).

## 6. Lexicon — the terms and symbols the work actually needs

Two lexicons, because they serve different machines: one for finding the literature, one for
selecting columns in a matrix. Both exist because a wrong string here silently produces a
plausible wrong answer.

### 6a. Literature search lexicon

| axis | use these | notes |
|---|---|---|
| disease | `NF2-related schwannomatosis`, `NF2-SWN`, `neurofibromatosis type 2`, `neurofibromatosis 2`, `bilateral vestibular schwannoma` | the pre-2022 names still dominate the corpus; search **both** eras or lose 20 years of work |
| gene | `NF2`, `NF2 gene`, `22q12` | bare `NF2` also matches "NF-2", nuclear factor 2, and NF-κB2 typography |
| protein | `merlin`, `schwannomin`, `moesin-ezrin-radixin-like protein` | `merlin` alone collides heavily with non-biological uses; pair it with `NF2` or `Hippo` |
| tumour | `vestibular schwannoma`, `acoustic neuroma`, `meningioma`, `spinal schwannoma`, `ependymoma` | "acoustic neuroma" is the older clinical term and is still in trial titles |
| pathway | `Hippo pathway`, `YAP`, `TAZ`, `WWTR1`, `TEAD`, `LATS1`, `LATS2` | `TAZ` is ambiguous — the gene is `WWTR1`; `TAZ` also names tafazzin (Barth syndrome) |
| context | `mesothelioma`, `NF2-null`, `NF2-deficient`, `merlin-deficient` | where the somatic loss gives enough cell lines to analyse |
| therapy | `bevacizumab`, `TEAD inhibitor`, `mTOR inhibitor`, `brigatinib` | |

**Disambiguation traps, in order of how much damage they do:**

1. **NF1 ≠ NF2.** Different gene (17q11 vs 22q12), different protein (neurofibromin, a
   RAS-GAP, vs merlin), different tumours (neurofibromas vs schwannomas/meningiomas). A
   bare "neurofibromatosis" query returns mostly NF1.
2. **`SMARCB1`/`LZTR1` schwannomatosis ≠ NF2-SWN.** Both are now "schwannomatosis" under the
   2022 nomenclature. Filter on the gene, never on the word.
3. **`TAZ` the coactivator (`WWTR1`) ≠ `TAZ` the tafazzin gene.** In a DepMap matrix keyed by
   symbol this one silently selects the wrong column.
4. **NF2 the gene ≠ NF-κB2 ≠ "NF2" as an abbreviation in physics/finance corpora.**

### 6b. Gene-symbol lexicon — what the analysis selects on

These are the strings the DepMap adapter will match against `SYMBOL (ENTREZID)` columns.
Stated here rather than buried in code so the positive control is auditable.

```
NF2_GENE        = ["NF2"]

HIPPO_POSITIVE  = ["YAP1", "WWTR1",                       # the effectors released by merlin loss
                   "TEAD1", "TEAD2", "TEAD3", "TEAD4",    # their transcription-factor partners
                   "LATS1", "LATS2",                      # the kinases merlin acts through
                   "STK3", "STK4",                        # MST2 / MST1
                   "SAV1", "MOB1A", "MOB1B"]              # scaffold and adaptors

MERLIN_ADJACENT = ["DCAF1", "VPRBP",                      # CRL4-DCAF1; same gene, two symbols
                   "MTOR", "RPTOR",                       # mTORC1 axis
                   "PTK2", "SRC",                         # FAK / Src
                   "ERBB2", "ERBB3", "PDGFRB"]            # RTK axis, weakest of the three
```

Three cautions that are easy to get wrong:

- **`WWTR1`, not `TAZ`.** See trap 3 above.
- **`STK3`/`STK4` are MST2/MST1** — the literature almost always uses the MST names and the
  matrix almost always uses the STK symbols.
- **`DCAF1` and `VPRBP` are the same gene**; which symbol appears depends on the release.

**How the positive control is scored:** the assertion is not "these genes rank first" — many
are pan-essential and Stage 3 should be pushing them down for that reason. It is that
`YAP1`/`WWTR1`/`TEAD` **rise in the NF2-null subgroup relative to NF2-wildtype lines** after
calibration. A control that cannot fail in one direction is not a control.

---

## 7. Does NF2 pass the four-question test?

From `expansion-map.md`:

1. Many candidate entities to rank? **Yes** — every gene in the genome.
2. Score estimated from noisy observations? **Yes** — Chronos effect per line.
3. Does the count vary? **Yes** — lines per gene, and the subgroup is small.
4. Is the aggregate a selection operator? **Yes** — top-k within the subgroup.

Four yeses. NF2 is a genuine fit, and a better one than the tauopathy entry it replaces in
`disease-expansion.md`: it needs no new data modality, it runs on a dataset already
validated in this repo, and it comes with a built-in positive control.

## 8. Sources to add

Deliberately left as an explicit to-do rather than filled with half-remembered citations:

- [ ] 2022 nomenclature update defining NF2-related schwannomatosis
- [ ] A current merlin/Hippo review, for section 3
- [ ] The DepMap release note for the version in `data/depmap/`
- [ ] Primary reports of NF2-loss → YAP/TAZ–TEAD dependency in mesothelioma
- [ ] Current TEAD-inhibitor clinical status
- [ ] The bevacizumab vestibular-schwannoma hearing-response literature

Each should arrive with a one-line statement of *what claim in this file it supports*.
