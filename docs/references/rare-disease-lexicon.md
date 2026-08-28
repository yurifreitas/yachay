# The rare-disease lexicon — unifying knowledge that was never written to be joined

> **Role:** the knowledge layer behind the rare-disease atlas in `web/`. Why the crosswalk
> exists, what the typed-unknown schema buys, and which sources have to be resolved before
> any of it counts as data.
> **Last revised:** 2026-08-27 · **State:** ⚠️ **schema demonstration with real examples,
> not a reference database.** Every identifier in `out/rare/lexicon.json` is written from
> working knowledge and carries a `confidence` field so the check can be prioritised.
>
> The single-disease version of the same idea is [`nf2.md`](nf2.md) §6.

---

## 0. The problem is fragmentation, not absence

Rare-disease knowledge is not mostly missing. It is mostly **unjoinable**. The same
disease carries a different identifier in every system that touches it, and none of those
systems is a superset of the others:

| System | Built for | Consequence |
|---|---|---|
| **Orphanet** (`ORPHA:`) | European rare-disease practice; prevalence, expert centres | the prevalence numbers live here and nowhere else |
| **OMIM** (`OMIM:`) | the genetics literature | a paper cites this; a registry does not |
| **MONDO** (`MONDO:`) | merging the others | its existence is the clearest evidence the problem is real |
| **HPO** (`HP:`) | phenotype terms | what makes two undiagnosed cases comparable at all |
| **ICD-11** | billing, mortality, statistics | first ICD with real rare-disease coverage; what health systems actually count |
| **GARD** | patient-facing summaries (NIH) | where families arrive first |
| **UMLS** (`C…`) | bridging clinical terminologies | the join of last resort |

A study indexed in one cannot be joined to a registry indexed in another without a
crosswalk. **The crosswalk is the lexicon**, and for a rare disease it is not a
convenience: the entire corpus may be a handful of papers, so a search keyed on the wrong
identifier or the wrong language finds nothing and concludes nothing exists.

## 1. "Rare" is not one definition

The threshold is set per jurisdiction, and **two of the four common ones are absolute
counts rather than rates** — so whether a disease is rare depends on where the patient
lives and how many people live there.

| Where | Rule | Basis |
|---|---|---|
| European Union | ≤ 5 in 10 000 | prevalence |
| United States | < 200 000 persons affected | absolute count |
| Japan | < 50 000 patients | absolute count |
| Australia | < 5 in 10 000 | prevalence |

**Ultra-rare has no single legal definition at all.** Both "< 1 in 50 000" and "< 1 in
1 000 000" appear in the literature, which is itself an instance of the problem this file
describes. The seed uses Orphanet's prevalence bands and states which convention it means.

## 2. The design decision: the unknown is a value, not a blank

This is the part worth transplanting to any other domain.

Roughly half of patients referred for rare-disease diagnosis end without a molecular
diagnosis, and a large share of *catalogued* diseases have no known causal gene, no
described mechanism, and no approved therapy. A schema that models those as missing values
produces a dashboard that **quietly under-reports the size of the problem** — the rows are
there, the cells are empty, and empty reads as "not applicable" rather than "nobody knows".

So every gap is typed:

```
gene       : symbol | UNKNOWN_GENE        catalogued, cause not found
prevalence : band   | UNKNOWN_PREVALENCE  never measured — not "zero"
mechanism  : text   | UNKNOWN_MECHANISM
therapy    : class  | NONE_APPROVED       does not exist yet, which is not the same
                                          as "unknown"
```

`NONE_APPROVED` and `UNKNOWN_MECHANISM` are deliberately different states. One is a gap in
the world, the other a gap in knowledge, and a shortlist that confuses them will propose
work on the wrong one.

**Two rows in the seed carry no ontology identifier at all** — an unsolved clinical
grouping and an undiagnosed multisystem case. They are the honest edge of the schema:
entries defined by what was *not* found are invisible to any pipeline keyed on
identifiers, which is exactly why they must appear in the atlas.

## 3. The lexical layer — names as searchability

Each entry carries its synonym set across languages and scripts, and this is not
decoration. For a common disease, a query in one language still reaches most of the
literature. For a rare one, the corpus may be five papers, and the ones written in
Japanese, German or Portuguese are simply lost to an English-only query.

The atlas marks non-Latin-script synonyms distinctly for that reason. It also carries the
naming traps that break searches outright, following the pattern already used for NF2:

- **the same disease under two names across a rename** — "neurofibromatosis type 2" and
  "NF2-related schwannomatosis" (2022 consensus). The old name still dominates the corpus.
- **an eponym that misdescribes the pathology** — the tumours in NF2-SWN are schwannomas
  and meningiomas, not neurofibromas.
- **a gene symbol colliding with an unrelated one** — `TAZ` the coactivator (`WWTR1`)
  against `TAZ` the tafazzin gene.

## 4. Field-level numbers, and what would confirm each

Carried in the seed with a per-claim confidence, and rendered in the atlas next to the
check that would verify it. **Two are quoted from a primary source; five are not.**

| Claim | Confidence | What would verify it |
|---|---|---|
| 350–400 M people live with a rare disease | **high** | quoted directly in the Broad/CTG announcement, 2026-07-21 |
| fewer than 1 in 20 has an approved treatment | **high** | same source |
| ~7 000–8 000 rare diseases catalogued | medium | Orphanet's current entity count |
| ~70–80 % are genetic in origin | medium | Orphanet / IRDiRC summary statistics |
| ~70 % have paediatric onset | medium | Orphanet / EURORDIS |
| ~half of referrals end undiagnosed | **low** | exome/genome diagnostic-yield literature |
| the diagnostic odyssey averages ~5 years | **low** | EURORDIS survey data |

## 4b. The instrument: what a case series of n can support

The atlas opens with a calculator rather than a summary, because the summary was the
problem. Ultra-rare literature is written in percentages drawn from single-digit series —
"seizures in 75% of patients" is three of four — and those percentages go on to shape
registries, endpoints and n-of-1 protocols.

Set `k` and `n`, and it reports the three numbers the paper does not print:

| At k = 3, n = 4 | |
|---|---|
| what the paper prints | **75%** |
| 95% Wilson interval | **30% – 95%** |
| width | **65 points** — cannot separate a majority from a minority |
| "an unobserved complication is rare" | the rule of three bounds it at **75%**, not zero |
| to bound that below 10% | **30 patients**; below 1%, **300** |

**Wilson rather than the normal approximation**, deliberately: at k = n = 4 the textbook
interval is [1, 1] — it claims certainty from four observations. Wilson does not degenerate
at the boundaries, which is the entire situation here.

**The rule of three is the number that surprises people.** A case series of five patients
with no serious adverse event is consistent with a true rate as high as 60%. "None
observed" is not "does not happen", and below about twenty patients it is barely evidence
at all. For a disease with a dozen patients alive, 30 and 300 are not sample sizes — they
are the reason ultra-rare evidence has to be built differently, and the reason CTG's
platform thesis (what is learned for one disease carries to the next) is a statistical
argument and not only a logistical one.

## 4c. The decision model — parameterised, and it shows its work

The dashboard's first section is a model, not a lookup. Set the constraints a programme
actually has — variant class, target tissue, disease mechanism, coding-sequence length,
patients known worldwide, months until intervention must begin — and set the weights that
reflect what *you* are optimising. It ranks six modalities and decomposes every score.

**Three states, kept distinct**, the same discipline as the typed unknowns in §2:

| state | meaning |
|---|---|
| scored high | fits, and here is what carried it |
| scored low | considered, and here is what sank it |
| **ruled out** | a hard constraint makes it impossible — *not* a low score |

A gene of 6 kb does not give AAV replacement a poor score; it makes it impossible, and the
model says so in a sentence (`the coding sequence is 6 kb; a single AAV carries about
4.7 kb`). Collapsing those two states is how a shortlist ends up containing something that
cannot be built.

**Measured behaviour**, verified in the browser rather than asserted:

| change | effect |
|---|---|
| CNS → liver | base editing **+59 → +81** — liver is the best-served tissue for delivery |
| variant → large deletion | base editing leaves the ranking entirely for **ruled out**; gene replacement enters the top three |
| mechanism → toxic gain of function | siRNA leaves the ruled-out list; ASO rises to +65 |

**The model grades its own confidence.** A `leaderStability` pass re-runs the ranking with
each weight moved ±0.5 and reports whether the leader survives. With the default
parameters it does not, and the panel says so:

> **fragile** — the leader changes if you move precision −0.5. Treat the ranking as a
> shortlist, not a choice.

That is the whole library's argument applied to itself: a ranking that flips under a small
change in an assumption is a shortlist, and calling it a decision is the error. **It is not
clinical guidance, and it is not validated against outcomes** — it is a structured way to
make assumptions explicit and disagree with them.

## 4d. Cell versus gene — lupus, and why it belongs here

The dashboard's fourth section exists because of a structural coincidence that turned out
to be an argument.

**This repository's own data is a matrix of cell lines × genes**, and its central statistic
is a top-k over the *cell lines* where a gene matters. The premise underneath everything
here is that a gene's effect is not a property of the gene — it is a property of the gene
in a context. Lupus is the clinical form of that premise, and it carries three things
nothing else in the atlas does.

**1. A disease that is rare in one country and not in another.** The EU threshold is 5 in
10 000, i.e. 50 per 100 000. Reported SLE prevalence spans roughly 20–150 per 100 000
depending on population, ancestry and case definition ⚠️. So the same disease crosses the
legal boundary depending on where the patient lives and partly on **who was counted** —
the cleanest possible illustration of §1. Prevalence and severity are substantially higher
in people of African, Hispanic and Asian ancestry, while most genetic studies were done in
European-ancestry populations: **the evidence base is thinnest where the burden is
heaviest.**

**2. An ultra-rare monogenic subset inside a common polygenic disease.** Twelve genes in
which one lesion is enough — complement (C1QA/C1R/C4A/C2), clearance (DNASE1L3), sensing
(TREX1, SAMHD1, IFIH1), tolerance (PRKCD, TNFAIP3, FAS). Two act by **gain** of function,
where more gene is the problem and the therapeutic logic inverts. `TNFAIP3` appears both as
a mendelian cause and as a small-effect population risk locus — the same gene at both ends
of the allelic-architecture spectrum, which is exactly the gap GaMBiT was launched to close
(`broad-institute-fit.md` §5).

**3. A cell axis where the headline result is a cell therapy.** CD19 CAR-T producing
drug-free remission in refractory SLE is a **cell** intervention, not a gene one ⚠️.

### What the arrangement surfaced

Laying the therapies out by the **cell** they act on rather than the molecule they bind
made something visible that a drug list hides:

> **Nothing points at the monocyte, the neutrophil, or the kidney.**

Every therapy in the seed targets a lymphoid cell or the interferon producer. The monocyte
is where the mechanism *starts* — failed clearance of dying cells is the debris that
becomes the antigen — and the kidney is where it becomes organ damage. The field treats the
amplifier and the antibody factory, which is where the tractable targets are, not where the
causal chain begins.

That is an observation about **this seed's arrangement**, not a claim that such programmes
do not exist, and the page says so in those words.

### Provenance, stated plainly

Gene–disease relationships above are well established. **The cell-type attributions are
simplifications** — most of these genes act in several cell types, and the primary-cell
column names where the mechanism is usually *described*, not the only place it operates.
The heatmap's scale is deliberately coarse (primary / plausible / not described) because a
finer one would imply a precision the sources do not have. Not clinical guidance.

## 5. Why this sits in a library about ranking

It does now, and at the sharpest point of contact.

`sieve`'s founding number is a record score measured on **one observation**, where pure
noise averages 0.845. Ultra-rare disease is that regime by construction: n is one, or four,
or twelve. The evidence calculator in §4b and the null calibration in `methodology.md`
Stage 1 are the same argument — *a statistic computed from very few observations is not the
quantity you think it is* — applied to a case series instead of to a screen.

`sieve` ranks candidates from noisy measurements. The rare-disease atlas ranks nothing: it
inventories what is known. They connect at one place, and it is a real one: **the entities
this library would rank are chosen from a catalogue whose gaps are patterned**. A gene
with no described mechanism is not a random member of the candidate set — it is
systematically under-studied, and under-studied entities have fewer observations, which is
the exact variable this library exists to correct for.

That is a hypothesis, not a result. It becomes testable the moment the identifiers are
resolved and the catalogue can be joined to a screen.

## 6. Before this is data

In priority order:

1. **Resolve every identifier** against Orphanet, OMIM, MONDO and HPO. The `confidence`
   field says which to check first: three rows are marked `none` and exist to demonstrate
   the no-identifier case rather than to assert one.
2. **Replace the seed with a real extract.** Orphanet publishes downloadable
   cross-reference files, and MONDO ships its mappings; neither needs to be hand-authored.
3. **Add HPO terms.** The phenotype layer is what makes undiagnosed cases comparable, and
   the seed has none.
4. **Decide the ultra-rare convention** and state it once, rather than inheriting the
   ambiguity described in §1.
