# NF2 biology — the deep review

> **Role:** the adversarial domain lane. It exists to answer one question the rest of the
> repository cannot answer for itself: **does this project's NF2 framing survive contact
> with the biology and the 2026 clinic?** It is also the source layer that
> [`../nf2.md`](../nf2.md) §8 left as an explicit to-do.
> **Last revised:** 2026-08-26 · **State:** complete; verdict in §6. Every citation below
> was resolved against the NCBI E-utilities `esummary` endpoint or the ClinicalTrials.gov
> v2 API rather than typed from memory. Items that could not be verified that way carry ⚠️
> and say what is missing.
>
> This is technical reference for prioritising research targets, **not clinical guidance**.
> Nothing here is a treatment recommendation.

**Verification convention used throughout.** *record* = bibliographic record verified
against PubMed E-utilities (title, authors, journal, volume, pages, DOI all match).
*abstract* = record verified and the abstract read. *full text* = the article body was
read. *registry* = the ClinicalTrials.gov v2 API record was read directly. *press* = a
company release or conference report only. ⚠️ marks a claim that is **not** verified at
the level a manuscript would need.

---

## 1. What is settled and what is contested in merlin biology

`../nf2.md` §3 describes the Hippo axis as settled and lists four others as "weaker and
less consistent". That is directionally right but too gentle: the four are not weaker
versions of the same thing. Two are mechanistically solid but **clinically dead**, one is
**prospectively falsified**, and one is **single-lab**. The distinction matters, because a
shortlist that recovers a clinically falsified axis has not found anything.

### 1a. Hippo / LATS / YAP–TAZ–TEAD — **settled**

Merlin acts on LATS1/2 rather than on MST1/2 kinase activity: Yin F, Yu J, Zheng Y, Chen Q,
Zhang N, Pan D, "Spatial organization of Hippo signaling at the plasma membrane mediated by
the tumor suppressor Merlin/NF2," *Cell* 2013;154(6):1342–55, DOI
10.1016/j.cell.2013.08.025, PMID 24012335, showed merlin **recruits** Wts/LATS to the
membrane. The mammalian genetics are equally hard: Zhang N, Bai H, David KK, … Pan D, "The
Merlin/NF2 tumor suppressor functions through the YAP oncoprotein to regulate tissue
homeostasis in mammals," *Dev Cell* 2010;19(1):27–38, DOI 10.1016/j.devcel.2010.06.015,
PMID 20643348, showed the liver phenotype of conditional *Nf2* loss is rescued by *Yap*
heterozygosity. (*record*; Yin abstract read.)

This axis is settled in the sense that matters here: it is genetically epistatic, replicated
across species, and it is the one that produced a drug. §1f below is the caveat that keeps
it from being a free pass.

### 1b. CRL4-DCAF1 nuclear axis — **real, but single-lab and mechanistically unresolved**

Li W, You L, Cooper J, … Giancotti FG, "Merlin/NF2 suppresses tumorigenesis by inhibiting
the E3 ubiquitin ligase CRL4(DCAF1) in the nucleus," *Cell* 2010;140(4):477–90, DOI
10.1016/j.cell.2010.01.029, PMID 20178741, and the follow-up Li W, Cooper J, Zhou L, …
Giancotti FG, "Merlin/NF2 loss-driven tumorigenesis linked to CRL4(DCAF1)-mediated
inhibition of the Hippo pathway kinases Lats1 and 2 in the nucleus," *Cancer Cell*
2014;26(1):48–60, DOI 10.1016/j.ccr.2014.05.001, PMID 25026211. The 2010 paper reports
that DCAF1 depletion blocks hyperproliferation of **patient-derived NF2 schwannoma cells** —
which is unusually good evidence for a target in the right lineage. (*record*; the
Cooper & Giancotti review, PMC4111995, read in full.)

Honest status: **contested by absence, not by refutation.** No published replication failure
or formal rebuttal was found ⚠️. What is true is that the model is largely confined to the
originating group's output, that the field's mainstream (Pan, McClatchey) explains the same
mouse phenotypes through membrane-proximal LATS regulation, and that reviews still describe
the compartment question as open. `DCAF1`/`VPRBP` is a defensible member of a positive
control set; it is not a settled fact.

### 1c. mTORC1 — **mechanism supported, monotherapy dead**

Two independent labs, same issue of *Mol Cell Biol*: James MF, Han S, Polizzano C, … Ramesh
V, "NF2/merlin is a novel negative regulator of mTOR complex 1…," 2009;29(15):4250–61, DOI
10.1128/MCB.01581-08, PMID 19451225; and López-Lago MA, Okada T, Murillo MM, Socci N,
Giancotti FG, "Loss of the tumor suppressor gene NF2, encoding merlin, constitutively
activates integrin-dependent mTORC1 signaling," 2009;29(15):4235–49, DOI
10.1128/MCB.01578-08, PMID 19451229. (*record*; López-Lago read in full via PMC2715795.)
The mechanism is not in doubt. The clinic is: see §3, where three separate everolimus
trials returned **zero** radiographic responses between them.

### 1d. FAK / Src — **prospectively falsified, and the single most important cautionary
tale in this file**

The biology is old and real (Poulikakos PI, Xiao GH, Gaur S, … Testa JR, *Oncogene*
2006;25(44):5960–8, DOI 10.1038/sj.onc.1209587, PMID 16652148). The synthetic-lethal claim
is explicit: Shapiro IM, et al., "Merlin deficiency predicts FAK inhibitor sensitivity: a
synthetic lethal relationship," *Sci Transl Med* 2014;6(237):237ra68, DOI
10.1126/scitranslmed.3008639, PMID 24848258. (*record*; quantitative details ⚠️
unverified — the full text was not accessible.)

It was tested prospectively and it failed. Fennell DA, et al., "Maintenance Defactinib
Versus Placebo After First-Line Chemotherapy in Patients With Merlin-Stratified Pleural
Mesothelioma" (**COMMAND**, NCT01870609), *J Clin Oncol* 2019;37(10):790–8, DOI
10.1200/JCO.2018.79.0543, PMID 30785827: 344 patients, **stratified by merlin status**,
median PFS 4.1 vs 4.0 months, no OS benefit, stopped for futility. The hypothesis lived
entirely in the merlin-low stratum and there was no signal there. (*record + abstract*; a
published critique letter exists, PMID 31329518, contents ⚠️ unread.)

**This is the exact failure mode `sieve` is supposed to prevent.** A cell-line-panel
selective dependency, published in a top journal, with a clean biomarker story, that did not
survive a randomised trial in the biomarker-defined population. Any `sieve` shortlist that
would have ranked `PTK2` highly should be read as a demonstration of the problem, not the
solution.

### 1e. RTK (ErbB / PDGFR) — **mechanism settled, effect size small**

Curto M, Cole BK, Lallemand D, Liu CH, McClatchey AI, "Contact-dependent inhibition of EGFR
signaling by Nf2/Merlin," *J Cell Biol* 2007;177(5):893–903, DOI 10.1083/jcb.200703010,
PMID 17548515 — merlin confines EGFR to a compartment where it can neither signal nor
internalise. Clinically this produced the field's most encouraging *small* numbers:
Karajannis MA, et al., "Phase II trial of lapatinib in adult and pediatric patients with
neurofibromatosis type 2 and progressive vestibular schwannomas," *Neuro Oncol*
2012;14(9):1163–70, DOI 10.1093/neuonc/nos146, PMID 22844108 — 4/17 evaluable volumetric
responses (23.5%), 4/13 hearing responses (30.8%). Real, reproducible in kind, not
practice-changing. (*record*.)

### 1f. Integrin / cortical actin / CD44 / ERM — **the oldest biology, still standing;
the Ser518 switch is contested**

Morrison H, Sherman LS, Legg J, … Herrlich P, "The NF2 tumor suppressor gene product,
merlin, mediates contact inhibition of growth through interactions with CD44," *Genes Dev*
2001;15(8):968–80, DOI 10.1101/gad.189601, PMID 11316791. Lallemand D, Curto M, Saotome I,
Giovannini M, McClatchey AI, "NF2 deficiency promotes tumorigenesis and metastasis by
destabilizing adherens junctions," *Genes Dev* 2003;17(9):1090–1100, DOI
10.1101/gad.1054603, PMID 12695331. Regulation via PAK: Kissil JL, Johnson KC, Eckman MS,
Jacks T, *J Biol Chem* 2002;277(12):10394–9, DOI 10.1074/jbc.M200083200, PMID 11782491.
(*record*.)

Caveat worth carrying: Xing W, et al., *Biochem Biophys Res Commun* 2017, DOI
10.1016/j.bbrc.2017.09.077, report that S518A/S518D mutants alter neither merlin's
conformation, nor its localisation, nor its growth suppression — against the standard
"S518 phosphorylation inactivates merlin" narrative ⚠️ (*abstract-level only*). The
scaffolding role is settled; **S518 as the master switch is contested.**

### 1g. The claim that should worry this project most

Yang H, Hall SRR, Sun B, et al., "NF2 and Canonical Hippo-YAP Pathway Define Distinct Tumor
Subsets Characterized by Different Immune Deficiency and Treatment Implications in Human
Pleural Mesothelioma," *Cancers* 2021;13(7):1561, DOI 10.3390/cancers13071561,
PMID 33805359 (*full text read*). Their central observation: genetic alteration of *NF2*,
**despite lowering merlin protein, is not associated with altered phospho-YAP**, whereas
*LATS2* mutation is. NF2-altered and canonically-Hippo-altered mesotheliomas are
overlapping but distinct subsets, and NF2 loss is linked to Hippo-YAP-**independent**
signalling (they name EGFR–RAS–ERK, B-cell-receptor signalling, DNA repair).

Read plainly: **`NF2` mutation status is a mediocre proxy for YAP/TAZ–TEAD dependency.**
That is a first-order problem for `out/NF2_FINDINGS.md`, which uses the Hippo axis as a
positive control for an `NF2`-mutation-defined subgroup. It supplies a fourth candidate
cause for that control's failure, alongside the three the run already lists — and unlike
those three, it is a cause that better data cannot fix. See §6.

### Summary table

| axis | mechanism | clinical outcome | status for a positive-control set |
|---|---|---|---|
| Hippo / YAP–TAZ–TEAD | settled, cross-species genetics | ORR 26–32% in mesothelioma (§3) | **use** — but see §1g |
| Cortical actin / CD44 / ERM | settled | never drugged directly | context, not a target |
| CRL4-DCAF1 (nuclear) | plausible, single-lab | never drugged | **use with a flag** |
| mTORC1 | settled (two labs) | 0 responses across 3 trials | negative control for translation |
| RTK (ErbB/PDGFR) | settled | 10–35% responses, small trials | weak positive |
| FAK / Src | real biology | **COMMAND: falsified in the biomarker stratum** | **use as a negative control** |
| PAK1/2 (Ser518 regulation) | scaffolding settled, switch contested | preclinical only | moderate |

---

## 2. The 2022 nomenclature, precisely

**The citation.** Plotkin SR, Messiaen L, Legius E, et al. "Updated diagnostic criteria and
nomenclature for neurofibromatosis type 2 and schwannomatosis: An international consensus
recommendation." *Genetics in Medicine* 2022;**24**(9):1967–1977. DOI
10.1016/j.gim.2022.05.007. PMID **35674741**. (*record verified via E-utilities*; the
criteria detail below is reconstructed from two secondary sources named at the end of this
section, and the *Genet Med* full text itself returned 403 ⚠️.)

**The nomenclature change.** "Neurofibromatosis type 2" is retired as a disease name.
*Schwannomatosis* becomes the umbrella term, subclassified by the causal gene:

| new term | replaces / means |
|---|---|
| **NF2-related schwannomatosis (NF2-SWN)** | the disease formerly called neurofibromatosis type 2 |
| **SMARCB1-related schwannomatosis** | a subtype of the umbrella, formerly "schwannomatosis"/"NF3" |
| **LZTR1-related schwannomatosis** | as above |
| **22q-related schwannomatosis** | 22q loss without an identified NF2/SMARCB1/LZTR1 variant |
| **schwannomatosis-NOS / -NEC** | not otherwise specified / not elsewhere classified |

The stated rationale is that the tumours are schwannomas, that the eponym invited confusion
with NF1, and that the conditions overlap phenotypically while differing genetically.

**The diagnostic criteria, as updated.** A definitive diagnosis of NF2-SWN requires **one**
of:

1. **Bilateral vestibular schwannomas**; or
2. an **identical NF2 pathogenic variant in ≥2 anatomically distinct NF2-related tumours**
   (schwannoma, meningioma, ependymoma); or
3. **two Major criteria**, or **one Major plus two Minor** criteria.

*Major:* unilateral vestibular schwannoma; a first-degree relative with NF2-SWN; ≥2
meningiomas; an NF2 pathogenic variant in unaffected tissue (blood or saliva).
*Minor (countable more than once):* ependymoma; schwannoma — where unilateral VS is the
major criterion, at least one schwannoma must be dermal. *Minor (counted once):* juvenile
subcapsular or cortical cataract; retinal hamartoma; epiretinal membrane under age 40;
meningioma.

**What changed from the 2011 Manchester criteria**, specifically:

- **"glioma" was replaced by "ependymoma"** — the tumour actually seen in NF2-SWN;
- **"neurofibroma" was removed** entirely, resolving the misleading eponym at the level of
  the criteria themselves;
- a **molecular diagnostic pathway** was added (test blood/saliva for *NF2*, *SMARCB1*,
  *LZTR1* first; if negative, test two or more anatomically unrelated tumours);
- **mosaicism was formally classified**: mosaic NF2-SWN is confirmed by a variant allele
  fraction clearly **<50%** in blood or saliva, **or** by a shared pathogenic variant in ≥2
  anatomically unrelated tumours with no variant detectable in unaffected tissue;
- an age cutoff (a proposed 70-year limit) was **considered and rejected**.

Mosaicism is not a footnote: **25–50% of individuals with a de novo *NF2* pathogenic variant
are somatic mosaics** (GeneReviews, *NF2-Related Schwannomatosis*, NBK1201, *full text
read*). Same source: estimated prevalence ~1:50,000, birth incidence ~1:28,000.

Sources for the criteria detail: Tamura R, Yo M, Toda M, "Historical Development of
Diagnostic Criteria for NF2-related Schwannomatosis," *Neurol Med Chir (Tokyo)*
2024;64(8):299–308, PMID 38897938 (*full text read*), and GeneReviews NBK1201. ⚠️ Both are
secondary to Plotkin 2022; before manuscript use, read the *Genet Med* table itself.

**Consequence for this repository.** `../nf2.md` §1 is correct and needs no change. The
practical addition is that the mosaic fraction is large, which is one more reason a
germline-mutation-table view of "NF2-null" under-calls the population — the same argument
`../nf2.md` §2 already makes for copy-number loss, arriving from a different direction.

---

## 3. The 2026 therapeutic landscape

All trial rows below were read from the **ClinicalTrials.gov v2 API** directly unless marked
otherwise. Efficacy numbers are quoted from the cited publication's abstract or full text.

### 3a. TEAD / Hippo inhibitors — all of it is in mesothelioma, none of it in NF2-SWN

| agent | sponsor | mechanism | trial | phase | population | efficacy (numbers) | status Aug 2026 | verification |
|---|---|---|---|---|---|---|---|---|
| **VT3989** | Vivace | oral pan-TEAD palmitoylation inhibitor | NCT04665206 | 1/2 | solid tumours, mesothelioma-enriched | **ORR 26%** in 47 mesothelioma pts at clinically optimised doses; with a UACR threshold applied (n=22) **ORR 32%, DCR 86%, mPFS 10 mo**. 172 pts total, 135 mesothelioma | Recruiting; enrolment 434; FDA orphan + fast track | *abstract* + *registry* |
| **VT3989 phase 3 ("sTEADfast")** | Vivace | same | **no NCT assigned publicly** | 3 | 2L/3L mesothelioma | not started | FDA "safe to proceed"; initiation announced for later in 2026 | ⚠️ *press only* — design, N, endpoints, NCT all unverified |
| **VT103** | Vivace | **TEAD1-selective** palmitoylation inhibitor | none | preclinical | — | tool compound only | no registered clinical trial found | *registry absence* |
| **IK-930** | Ikena | TEAD1-selective palmitoylation inhibitor | NCT05228015 (± osimertinib) | 1 | NF2-deficient mesothelioma, EHE, YAP/TAZ fusions | **no response data ever published** | **TERMINATED**, 67 of 198 planned enrolled | *registry* + ⚠️ *press* for the reason (company framed it as portfolio strategy; no efficacy/safety failure disclosed) |
| **IAG933** | Novartis | **YAP/TAZ–TEAD PPI disruptor** (not palmitoylation) | NCT04857372 | 1 | mesothelioma; NF2/LATS1/LATS2-mutant; YAP/TAZ fusions | none published | Active, not recruiting; n=137; **monotherapy only, no combination arm registered** | *registry* |
| **SW-682** | SpringWorks | TEAD inhibitor | NCT06251310 | 1a/1b | solid tumours incl. mesothelioma | none reported | Recruiting, n=186; a Part-2 cohort reserves an unnamed combination partner | *registry* |
| **BPI-460372** | Betta | covalent irreversible TEAD1/3/4 | NCT05789602 | 1 | solid tumours | none reported | Recruiting; registry entry stale since Jan 2025 | *registry* |
| **ISM6331** | Insilico Medicine | pan-TEAD (AI-discovered) | NCT06566079 | 1 | mesothelioma + solid tumours | none reported | Recruiting, n=100 | *registry* |
| **TYK-01054** | TYK Medicines | TEAD inhibitor | NCT07282873 | 1/2 | solid tumours incl. mesothelioma | — | Not yet recruiting | *registry* |
| **GNE-7883** | Genentech | allosteric pan-TEAD | — | preclinical | — | — | no clinical record found; **do not cite as clinical-stage** | ⚠️ |

The VT3989 anchor publication: **Yap TA, Kwiatkowski DJ, Dagogo-Jack I, … Kindler HL,
"YAP/TEAD inhibitor VT3989 in solid tumors: a phase 1/2 trial," *Nat Med*
2025;31(12):4281–4290, DOI 10.1038/s41591-025-04029-3, PMID 41111090.** This resolves the
⚠️ that `../state-of-the-art.md` §2 left open on the ESMO/news numbers: the ORR figures
there are confirmed by the record. Toxicity is dominated by reversible proteinuria and a
rising urine albumin:creatinine ratio, plus peripheral oedema and fatigue.

**One number from that trial deserves its own line, because it is the hinge of this whole
document: benefit was observed in patients both with and without *NF2* mutations.** The
drug works; *NF2* status does not cleanly select who it works in. That is the clinical
echo of §1g.

### 3b. NF2-related schwannomatosis — the actual disease

| agent | sponsor / PI | class | trial | phase | efficacy (numbers) | status | verification |
|---|---|---|---|---|---|---|---|
| **Bevacizumab** (index) | MGH / Plotkin | anti-VEGF mAb | pilot, n=10 | — | tumour shrank in **9/10**, median best volumetric reduction **26%**; of 7 hearing-evaluable: **4 improved, 2 stable, 1 progressed** | landmark 2009 | *abstract read* — Plotkin SR et al., *NEJM* 2009;361(4):358–67, DOI 10.1056/NEJMoa0902579, PMID 19587327 |
| **Bevacizumab** (induction) | NF Clinical Trials Consortium | anti-VEGF 10 mg/kg q2w × 6 mo | NCT01767792 | 2 | n=22 enrolled, 19 completed induction: **hearing response 8/19 (42%)**, **radiographic response 4/19 (21%)** | completed | *record* — PMID 31626572 |
| **Bevacizumab** (maintenance) | same | anti-VEGF 5 mg/kg q3w × 18 mo | same programme | 2 | n=20: **freedom from hearing loss 95% @48 wk, 89% @72 wk, 70% @98 wk**; freedom from tumour growth **89% @98 wk**; 3/20 (15%) discontinued for AEs | published 2023 | *abstract read* — Plotkin SR et al., *Neuro Oncol* 2023;25(8):1498–1506, DOI 10.1093/neuonc/noad066, PMID 37010875 |
| **Bevacizumab** (meta-analysis) | — | — | — | — | radiographic partial regression **41% (95% CI 31–51)**, no change 47%, progression 7%; **hearing improvement 20% (95% CI 9–33)**, stable 69%; **serious toxicity 17% (95% CI 10–26)** | 2019 | *abstract read* — Lu VM et al., *J Neurooncol* 2019;144(2):239–248, DOI 10.1007/s11060-019-03234-8, PMID 31254266 |
| **Brigatinib** | MGH / Plotkin, CTF | ALK/EGFR-family TKI, repurposed | **INTUITT-NF2, NCT04374305** | 2, adaptive platform-basket | n=40, median f/u 10.4 mo: response **10% target / 23% all tumours**; meningioma 25%, non-VS schwannoma 20%; **hearing improvement in 35% of eligible ears**; no grade 4/5 treatment-related AEs | arm complete and reported | *record* — *NEJM* 2024;390(24), DOI 10.1056/NEJMoa2400985, PMID 38904277 |
| **Brigatinib**, updated | same | same | same | 2 | median f/u 23 mo: overall radiographic response **28%** (ependymoma 60%, non-VS 31%, meningioma 28%, VS 22%); **24-mo freedom from progression 73%** | SNO 2025 | ⚠️ *conference abstract* (*Neuro Oncol* 2025;27(Suppl 5):v137, CTNI-50) |
| **Neratinib** | MGH / Plotkin | irreversible pan-erbB TKI | INTUITT-NF2 arm | 2 | interim n=20: response **10% target / 13% all**; non-VS schwannoma **35%**; **VS 0%, ependymoma 0%**; 5 grade-3 AEs, all diarrhoea | fully enrolled, interim Nov 2025 | ⚠️ *conference abstract* (CTNI-48) |
| **Retifanlimab + bevacizumab** | MGH / Plotkin | anti-PD-1 + anti-VEGF | INTUITT-NF2 arm | 2 | **no efficacy reported** | arm active | ⚠️ *registry only* |
| **Everolimus** (Karajannis) | NYU | mTORC1 | NCT01419639 | 2 | **0/9 evaluable** imaging or hearing responses; closed early per stopping rules | negative | *record* — *Neuro Oncol* 2014;16(2):292–7, DOI 10.1093/neuonc/not150, PMID 24311643 |
| **Everolimus** (Goutagny) | AP-HP | mTORC1 | NCT01490476 | 2 | **0 responses ≥20%** at 12 mo; median annualised growth **67%/yr → 0.5%/yr on drug** | cytostatic, not cytotoxic | ⚠️ *record-level* — PMID 25567352; 4-yr follow-up PMID 28434114 |
| **Everolimus** (UCLA) | Jonsson CCC | mTORC1 | prospective, n=12 | 2 | **0 radiographic responses**; median annual growth **77.2% → 29.4%**; hearing stable in 7/8 | published 2024 | ⚠️ *record-level* — PMID 38372904 |
| **Crizotinib** | UAB | ALK/MET/ROS1 TKI | NCT04283669 | 2 | **primary endpoint negative: 0/9 responders**; 5/9 stopped for progression | completed; results posted Mar 2026 | *registry results record* |
| **Axitinib** | NYU | VEGFR/PDGFR/KIT TKI | NCT02129647 | 2 | n=12 (10 evaluable): **2 objective volumetric responses**, best −53.9%; **3 hearing responses, 1 sustained** | published 2025 | ⚠️ *record-level* — PMID 40575410 |
| **Selumetinib** | Cincinnati Children's | MEK1/2 | NCT03095248 | 2 | **terminated for futility**; VS stratum hearing response 0/1 | terminated May 2024 | *registry*; ⚠️ one posted efficacy field is internally inconsistent with the futility termination — treat as a coding artefact |
| **VEGFR1/2 peptide vaccine** | Keio (Tamura/Toda) | therapeutic vaccine | jRCTs031180184 (Japan) | 1/2 | n=16 completing: **PR in >1 schwannoma in 4, minor response 5, SD 4**; word recognition improved in 5/13 at 6 mo; hearing progression 0.168 vs 0.364 dB/mo | published 2024 | *abstract* — *JCO* 2024, PMID 38776485 |
| **Aspirin vs placebo** | Mass Eye and Ear | COX inhibitor | NCT03079999 | 2, **randomised placebo-controlled** | none yet | active, not recruiting; n=97; completion est. **Feb 2029** | *registry* |
| **PRIME-NF2 platform** | Beijing Tiantan | selumetinib, luvometinib, serplulimab | NCT07713745 | 2 | — | not yet recruiting; n=200, runs to 2036 | *registry* |

**Three structural facts about this table, which matter more than any individual row.**

1. **No TEAD inhibitor is in a registered trial in NF2-related schwannomatosis.** A full
   registry query on that condition returns zero TEAD studies. The entire TEAD programme is
   in mesothelioma and unselected solid tumours. `../state-of-the-art.md` §2 says "the
   pathway our positive control tests is the pathway the clinic is now betting on" — true,
   but the clinic is betting on it **in the malignant somatic context, not in the germline
   disease this project names.**
2. **There is no randomised evidence for bevacizumab in NF2-SWN.** Every prospective study
   is single-arm. The first randomised readout in the disease is the aspirin trial, in 2029.
3. **mTOR is exhausted.** Three independent everolimus trials, zero radiographic responses
   between them, and a consistent cytostatic-not-cytotoxic signature. If a `sieve` shortlist
   ranks `MTOR` or `RPTOR` highly, that is a *known-negative* recovery, not a hit —
   analytically useful, therapeutically finished.

---

## 4. Resistance and combination — the open clinical question

This is the section that justifies the project's positioning in
`../state-of-the-art.md` §2. That framing is correct and the literature now supports it with
specifics: **TEAD monotherapy resistance is real, is largely non-genetic, and converges on a
small number of routes.**

### 4a. Verified resistance mechanisms

| route | mechanism | compound and model | source |
|---|---|---|---|
| **MAPK / AP-1 reactivation** | resistant cells **restore YAP/TEAD chromatin occupancy** with additional **FOSL1** binding and increased MAPK activity; FOSL1 is required for YAP/TEAD chromatin binding | GNE-7883, NF2-null mesothelioma lines ⚠️ (line identity from secondary summaries) | Paul S, Hagenbeek TJ, … Dey A, *Nat Commun* 2025;16:1743, DOI 10.1038/s41467-025-56634-y, PMID 39966375 (*abstract*) |
| **MAPK, Hippo and JAK–STAT — from an unbiased screen** | **genome-wide CRISPR resistance screens in mesothelioma lines** under TEAD palmitoylation inhibitors; MAPK hyperactivation reinstates a subset of YAP/TAZ target genes | Vivace-series compounds; mesothelioma lines + lung PDX | Kulkarni A, … Vissers JHA, Harvey KF, *EMBO Rep* 2024;25(9):3944–3969, DOI 10.1038/s44319-024-00217-3, PMID 39103676 (*abstract*; ⚠️ **gene-level hits not verified — do not cite specific genes from this screen without the full text**) |
| **PI3K/AKT via VGLL3→SOX4** | TEAD inhibition gives only **transient cell-cycle arrest without cell death**; VGLL3 activates a SOX4/PI3K/AKT survival axis | MGH-CP1, large cell-line panel | Sun Y, … Wu X, *Nat Commun* 2022;13:6744, DOI 10.1038/s41467-022-34559-0, PMID 36347861 (*abstract*) |
| **MYC-driven TEAD independence** | a subset of Hippo-inactivated mesothelioma lines are **intrinsically resistant**; MYC overexpression confers resistance in vitro and in vivo | K-975, mesothelioma panel | Akao K, … Sekido Y, *Mol Cancer Ther* 2025;24(5):709–719, DOI 10.1158/1535-7163.MCT-24-0308, PMID 39686607 (*abstract*) |
| **Coactivator switching to VGLL1** | TEAD transcription proceeds **without YAP**, driven by VGLL1; EGFR is a VGLL1/TEAD target | breast cancer, endocrine therapy | Gemma C, … Ali S, *Cancer Res* 2024;84(24):4283–4297, DOI 10.1158/0008-5472.CAN-24-0013, PMID 39356622 (*abstract*) |
| **Coactivator switching to TAZ** | SOX10 loss drives TEAD targets via **TAZ (WWTR1)**, not YAP; sufficient for drug tolerance | OPN-9643/OPN-9652, melanoma MRD models | Ott CA, … Aplin AE, *Nat Commun* 2025;16:9655, DOI 10.1038/s41467-025-64682-7, PMID 41193428 (*abstract*) |

**Explicitly not found, and therefore an open gap rather than a known mechanism:** ⚠️ no
published report of **palmitate-pocket TEAD resistance mutations**. Targeted searches
returned nothing on point. Also unverified as TEAD-inhibitor resistance routes: YAP
amplification, AXL, interferon/immune escape, SRC.

### 4b. Combination partners — clinical

From the registry, verified directly:

- **NCT04665206 (VT3989)** registers combination interventions with **nivolumab +
  ipilimumab**, **osimertinib**, and **pemetrexed/carboplatin**. Combination cohorts are
  recruiting.
- **NCT05228015 (IK-930)** registered **IK-930 + osimertinib**; the trial is terminated.
- **NCT04857372 (IAG933)** is **monotherapy only** — the MAPK combination rationale for
  IAG933 is preclinical, not registered.
- **NCT06251310 (SW-682)** reserves a Part-2 cohort for a combination partner "identified
  based on Part 1 data" — unnamed.

### 4c. Combination partners — preclinical, with the strongest evidence first

1. **MEK / MAPK.** Two independent groups plus Novartis. Kulkarni/Harvey (PMID 39103676)
   report TEADi + MEKi synergy across mesothelioma and lung lines and in lung PDX in vivo;
   Paul/Dey (PMID 39966375) report MAPK inhibitors overcome GNE-7883 resistance; Chapeau EA,
   … Schmelzle T, *Nat Cancer* 2024;5(7):1102–1120, DOI 10.1038/s43018-024-00754-9,
   PMID 38565920 report that IAG933 combined with RTK inhibitors, KRAS-selective inhibitors
   and MAPK inhibitors gives more durable responses.
2. **PI3K / AKT / mTOR.** Sun/Wu (PMID 36347861) for AKT. Independently, the best unbiased
   source for a combination list: Evsen L, Morris PJ, Thomas CJ, Ceribelli M, "Comparative
   Assessment and High-Throughput Drug-Combination Profiling of TEAD-Palmitoylation
   Inhibitors in Hippo Pathway Deficient Mesothelioma," *Pharmaceuticals* 2023;16(12):1635,
   DOI 10.3390/ph16121635, PMID 38139762 (NCATS) — six TEAD inhibitors benchmarked, **all
   with limited single-agent efficacy**; VT-103 screened against ~3000 oncology drugs;
   robust synergies with **glucocorticoid-receptor agonists, MEK1/2 inhibitors, mTOR
   inhibitors and PI3K inhibitors**. (*abstract*; ⚠️ the full synergy hit list needs the
   full text, which is open access.)
3. **KRAS G12C, bidirectionally.** Edwards AC, … Der CJ, *Cancer Res* 2023;83(24):4112–4129,
   DOI 10.1158/0008-5472.CAN-23-2994, PMID 37934103; Hagenbeek TJ, … Dey A, *Nat Cancer*
   2023;4(6):812–828, DOI 10.1038/s43018-023-00577-0, PMID 37277530.
4. **EGFR / osimertinib** — the YAP-driven persister rationale. Kurppa KJ, … Jänne PA,
   *Cancer Cell* 2020;37(1):104–122.e12, DOI 10.1016/j.ccell.2019.12.006, PMID 31935369;
   Pfeifer M, … McDermott U, *Commun Biol* 2024;7:497, DOI 10.1038/s42003-024-06190-w,
   PMID 38658677. **Important caveat:** Sanchez DJ, et al., *Mol Cancer Ther* 2026 (online
   ahead of print), DOI 10.1158/1535-7163.MCT-25-1267, PMID 42525965, report that AZ'4331
   enhances osimertinib in vitro but the benefit translates in vivo **only when osimertinib
   is dosed below clinically relevant levels**.
5. **PAK — and this one is in the right lineage.** Benton D, Chow HY, Karchugina S, Chernoff
   J, "Synergistic effect of PAK and Hippo pathway inhibitor combination in NF2-deficient
   Schwannoma," *PLoS One* 2024;19(7):e0305121, DOI 10.1371/journal.pone.0305121,
   PMID 39083549 (*full text read*). FRAX-1036 (group I PAK) combined with TED-347, IK-930 or
   NSC682769, in HEI-193, mouse SC4, and **CRISPR-generated NF2-null human Schwann cells**;
   mean ZIP and Bliss synergy scores >30 in the NF2-null human Schwann cells. This is the
   only combination in the list tested in schwannoma models.
6. **Metabolic rewiring after YAP/TAZ inhibition.** White SM, et al., "YAP/TAZ Inhibition
   Induces Metabolic and Signaling Rewiring Resulting in Targetable Vulnerabilities in
   NF2-Deficient Tumor Cells," *Dev Cell* 2019;49(3):425–443.e9, DOI
   10.1016/j.devcel.2019.04.014, PMID 31063758 — YAP/TAZ depletion shifts cells off
   glycolysis onto mitochondrial respiration with ROS accumulation, creating
   oxidative-stress-induced death under nutrient stress. ⚠️ *record-level plus a secondary
   summary of the mechanism; full text 403'd.* Conceptually this is the same shape as the
   G6PD/ACSL3 redox finding in §5.

**Not verified, despite being commonly assumed:** ⚠️ TEADi + CDK4/6, TEADi + BET/BRD4,
TEADi + PARP. Targeted searches returned nothing on point. ⚠️ TEADi + immune checkpoint
blockade is *clinically registered* but has no clean preclinical paper behind it that could
be verified. ⚠️ **No published FAK + TEAD combination study in NF2-null mesothelioma
exists** — despite both hypotheses having been prominent in the same disease.

### 4d. What this means for a `sieve` shortlist

The clinically useful question is now narrow and stateable: **what does an NF2-null,
TEAD-inhibited cell still need?** The published resistance routes are MAPK/AP-1, PI3K/AKT,
MYC, and coactivator switching — which is to say, they are *pathway* answers, produced by
hypothesis-driven work and by one CRISPR screen done **under drug**. A selective-dependency
ranking done **without drug** cannot recover an adaptive resistance mechanism; it can only
recover a baseline co-dependency. That is a real but bounded contribution, and this document
is the place to say so rather than let the shortlist imply more.

---

## 5. Published NF2-null dependencies — an expanded positive-control set

Tiered by how much the evidence would survive being wrong. `../nf2.md` §6b's
`HIPPO_POSITIVE` and `MERLIN_ADJACENT` lists remain valid; this extends and, in two places,
corrects them.

### Tier A — unbiased genome-wide screen, isogenic *NF2* pair, **in the Schwann-cell lineage**

| gene | direction | model system | source | confidence |
|---|---|---|---|---|
| **G6PD** | NF2-KO cells depend on it | immortalised human Schwann line **ipn02.3 2λ**, isogenic CRISPR NF2-KO vs WT; TKO v3 library, 89,916 sgRNAs / 17,232 genes | Kyrkou A, et al., "G6PD and ACSL3 are synthetic lethal partners of NF2 in Schwann cells," *Nat Commun* 2024;15(1):5115, DOI 10.1038/s41467-024-49298-7, PMID 38879607 | **high** — *full text read*; in vivo validated: inducible shRNA **completely regressed** NF2-KO schwannoma xenografts in NSG mice over 25 weeks; rescued by N-acetylcysteine (oxidative-stress mechanism) |
| **ACSL3** | as above | same screen | same | **high** — mechanism is ferroptosis; rescued by liproxstatin |
| *(ME1)* | mechanistic partner, **not a primary screen hit** | same | same | medium — listed for completeness; NF2-KO cells have lower NADPH/NADP⁺ and reduced antioxidant enzyme expression |

Authors' own caveat, stated in the paper: two immortalised lines and one primary line were
testable, because NF2-WT human Schwann cells are scarce.

**This is the single most important row in the file for §6.** It is the only unbiased
genome-wide NF2 synthetic-lethal screen in the disease's own cell type, and its top hits —
`G6PD`, `ACSL3` — **do not appear anywhere in the mesothelioma NF2-dependency literature.**

### Tier B — mechanism plus in vivo, NF2-selective

| gene | model system | source | confidence |
|---|---|---|---|
| `YAP1`, `WWTR1`, `TEAD1–4` | mesothelioma lines and xenografts; **and**, importantly, NF2-null schwannoma and meningioma | Laraba L, et al., "Inhibition of YAP/TAZ-driven TEAD activity prevents growth of NF2-null schwannoma and meningioma," *Brain* 2023;146(4):1697–1713, DOI 10.1093/brain/awac342, PMID **36148553** | **high** |
| `DHODH`, `CAD` | NF2-deficient pleural mesothelioma, orthotopic in vivo; minimal effect on NF2-WT | Xu D, et al., "De novo pyrimidine synthesis is a collateral metabolic vulnerability in NF2-deficient mesothelioma," *EMBO Mol Med* 2025;17(9):2258–2298, DOI 10.1038/s44321-025-00278-4, PMID 40707702 | **medium-high** — *record*; mechanism NF2→YAP→CAD/DHODH |
| `PAK1`, `PAK2` | RNAi + small molecule (FRAX597) + GEMM, NF2-associated schwannoma | Licciulli S, et al., *J Biol Chem* 2013;288(40):29105–14, DOI 10.1074/jbc.M113.510933, PMID 23960073; plus PMID 39083549 (§4c) | **medium-high** — multi-model, in-lineage |
| `DCAF1` (`VPRBP`) | patient-derived NF2 schwannoma cells; merlin-deficient lines | Li W, et al., *Cell* 2010, PMID 20178741 (§1b) | **medium** — strong genetics, single lab, no drug |
| `MARK2`, `MARK3` | paralog co-targeting CRISPR screens across carcinoma/sarcoma; catalytic co-dependency of YAP/TAZ, in vivo regression | Klingbeil O, et al., "MARK2/MARK3 Kinases Are Catalytic Codependencies of YAP/TAZ in Human Cancer," *Cancer Discov* 2024;14(12):2471–2488, DOI 10.1158/2159-8290.CD-23-1529, PMID 39058094 | **medium** — note it is stratified by **YAP/TAZ dependency, not by NF2 status** |
| `MTOR`, `RPTOR` | merlin-deficient meningioma cells, arachnoidal cells | James 2009, PMID 19451225 (§1c) | **medium mechanism / low translation** — see §3b |
| `SGK1` | kinome screen, NF2-deficient meningioma | *Oncotarget* 2015, PMC4627286 ⚠️ *record-level only* | **low-medium** |

### Tier C — preclinically claimed, **clinically falsified**

| gene | why it is here |
|---|---|
| `PTK2` (FAK) | Shapiro 2014 (PMID 24848258) claimed a merlin-FAK synthetic lethal relationship; **COMMAND** (PMID 30785827, NCT01870609) tested it prospectively in 344 merlin-stratified patients and found nothing. Independent orthogonal arrival at FAK exists (brigatinib proteomics, *PLoS One* 2021, PMC8282008 ⚠️ *record-level*), which makes the negative more instructive, not less. |

**Recommendation: `PTK2` belongs in the control set as a *falsification* control.** If a
calibrated ranking places `PTK2` in the NF2-null shortlist, that is not corroboration —
it is `sieve` reproducing a published result that a randomised trial has already refuted.

### Negative controls / confound detectors — genes that will light up for the wrong reason

| genes | why they will appear | evidence |
|---|---|---|
| `CDK4`, `CDK6`, `CCND1`, `RB1` | Palbociclib alone inhibited **23 of 23** mesothelioma lines; insensitivity tracked **CDKN2A/RB1/CCNE1** status, not NF2 | ⚠️ *record-level* (bioRxiv 2022.04.11.487857; published version PMC10994244) |
| `PRMT5`, `MAT2A`, `RIOK1` | **MTAP/CDKN2A co-deletion.** ~74% of pleural mesotheliomas carry CDKN2A homozygous deletion, and MTAP is co-deleted in ~91% of those. MTAP loss → MTA → partial PRMT5 inhibition → PRMT5/MAT2A synthetic lethality | ⚠️ *record-level* (Clin Cancer Res 2003;9:2108) — but see the measured confirmation below |
| `BAP1`-axis genes | BAP1 and NF2 co-occur in mesothelioma; a combined *Bap1* + *Nf2* + *Cdkn2ab* mouse develops rapid-onset mesothelioma (PMID 32271879 ⚠️ *record-level*) — the three are functionally entangled by construction |

**Measured directly against this repository's own data on disk (2026-08-26), not taken from
the literature.** Defining NF2-null on the screened panel as a damaging *NF2* mutation **or**
`OmicsCNGene` NF2 < 0.3 gives 35 of 1178 screened lines. Among lines with copy-number data
available:

| feature | NF2-null | NF2-wildtype |
|---|---|---|
| CDKN2A deep deletion | **68.4%** (13/19) | 29.2% (117/401) |
| MTAP deep deletion | **36.8%** (7/19) | 18.7% (75/401) |

⚠️ **Caveat on those numbers:** the local `OmicsCNGene.csv` parses to only **580 rows**,
which is well short of a full DepMap CN release — the file appears to be a partial download,
so CN was available for 420 of 1178 screened lines. The direction of the enrichment is
consistent with the published MTAP/CDKN2A co-deletion literature; the magnitude should be
recomputed on a complete file before it is quoted anywhere else.

### Two corrections to leads that did not survive checking

- ⚠️ **Project DRIVE does not name NF2 mutation as the YAP1 dependency biomarker.** McDonald
  ER 3rd, et al., *Cell* 2017;170(3):577–592.e10, DOI 10.1016/j.cell.2017.07.005,
  PMID 28753431. The paper's stated best predictor of YAP1 sensitivity is **low expression of
  the paralog `WWTR1`/TAZ**. The NF2 framing was layered on by later reuse of the DRIVE
  data. Do not cite DRIVE for an NF2–YAP1 biomarker claim.
- ⚠️ **The Synodos for NF2 drug screen found hits that are not NF2-selective.** Synodos for
  NF2 Consortium, "Traditional and systems biology based drug discovery for the rare tumor
  syndrome neurofibromatosis type 2," *PLoS One* 2018;13(6):e0197350, DOI
  10.1371/journal.pone.0197350, PMID 29897904. Top compounds across isogenic schwannoma and
  meningioma systems were **GSK2126458 (omipalisib, PI3K/mTOR), panobinostat (HDAC), and
  CUDC-907 (fimepinostat)** — but the authors state that **merlin status did not
  significantly influence response**, and in vivo only meningioma, not schwannoma,
  responded. These are NF2-tumour-active compounds, not NF2-selective dependencies. They do
  **not** belong in a synthetic-lethality positive control.
- ⚠️ **No published critique of NF2 DepMap dependencies as lineage-confounded was found.**
  Multiple targeted searches returned nothing standalone. Either it does not exist or it is
  buried in a supplement. If this repository can measure it, that is an actual gap.

---

## 6. EXTERNAL VALIDITY — mesothelioma cell lines versus schwannoma

This section answers question 4 of [`README.md`](README.md). **The framing does not survive
intact. It survives in a narrowed form, and the narrowing has to be written down.**

### 6a. The hardest fact, measured on the data on disk

`data/depmap/Model.csv` contains **2105 models**. Of those:

- **schwannoma cell lines: zero.** No `OncotreePrimaryDisease` or `OncotreeSubtype` value in
  the file contains "schwannoma", and none contains "nerve sheath".
- meningioma cell lines: **4** (CH157MN, IOMMLEE, F5, HKBMM), of which **3** appear in
  `CRISPRGeneEffect.csv`.
- pleural lines screened: **21**.

So the disease this project names — a benign, germline, Schwann-cell tumour syndrome — has
**no representation whatsoever** in the dataset the project analyses. It is represented, at
best, by three meningioma lines, which are the *other* NF2-SWN tumour type and are
themselves malignant-panel derivatives.

A second measured fact cuts against a claim in `../nf2.md` §5 and `out/NF2_FINDINGS.md`:
mesothelioma is **not** the dominant lineage in the NF2-null subgroup. On the mutation-only
definition the top lineage is Lung (6 of 32); on the mutation-or-deletion definition it is
Lung (7 of 35), with Pleura at 4. Pleura is strongly *enriched* (5.3×) but is not the
plurality. The lineage confound documented in `../nf2.md` §3 Stage 3 is real, but the
mechanism named for it is imprecise — and the measured CDKN2A/MTAP co-deletion enrichment in
§5 is a better candidate for what is actually distorting the ranking.

### 6b. What transfers

- **YAP/TAZ–TEAD does transfer, and this is well demonstrated.** Laraba L, et al., *Brain*
  2023;146(4):1697–1713, DOI 10.1093/brain/awac342, PMID 36148553 (*full text read via the
  journal page*) took TEAD palmitoylation inhibitors originally developed against NF2-null
  mesothelioma and showed they work in **Periostin-Cre;Nf2^fl/fl** and **P0-Cre;Nf2^fl/fl**
  mouse schwannoma, in primary human NF2-null schwannoma and meningioma cells, and in
  meningioma lines — significant tumour-volume reduction at 9 months, 73% and 52%
  proliferation reductions in vestibular ganglia at 3 months, increased apoptosis by TUNEL.
  They also show YAP and TAZ have **overlapping but distinct** roles (ALDH1A1 regulation is
  TAZ-dependent), which is a caution against treating `YAP1` and `WWTR1` as interchangeable
  in a gene set. This is a genuine mesothelioma → schwannoma transfer, and it is the reason
  the Hippo positive control is defensible at all.
- **PAK1/PAK2 transfers**, and in the correct direction: it was established in schwannoma
  first and works there (PMID 23960073, PMID 39083549).

### 6c. What does not transfer

1. **FAK.** Established in merlin-deficient mesothelioma, falsified in merlin-stratified
   mesothelioma patients (COMMAND). It never even reached the germline disease.
2. **The mesothelioma-derived metabolic dependencies and the schwannoma-derived ones are
   different genes.** The pleural-mesothelioma NF2 vulnerability is de novo pyrimidine
   synthesis — `CAD`, `DHODH` (PMID 40707702). The Schwann-cell NF2 vulnerability from the
   only in-lineage genome-wide screen is redox and lipid — `G6PD`, `ACSL3` (PMID 38879607).
   Both are metabolic, both are NF2-selective in their own system, and **they do not
   overlap.** That is about as direct a demonstration of limited cross-lineage transfer as
   the literature offers.
3. **Everything driven by CDKN2A/MTAP co-deletion.** That co-deletion is a feature of
   malignant mesothelioma genome instability. It is not a feature of a benign schwannoma with
   a near-diploid genome and a two-hit *NF2* lesion. Any `PRMT5`/`MAT2A`/`RIOK1` signal from
   an NF2-null DepMap contrast is a mesothelioma-genome artefact with no schwannoma meaning.
4. **CDK4/6 and the proliferation machinery.** A CRISPR fitness screen measures dropout in
   fast-dividing immortalised cells over ~21 days. Vestibular schwannomas are slow-growing
   over years — GeneReviews states untreated tumours "may be slow growing and may not
   require active intervention in the short term", and the everolimus trials measured
   *annualised* growth rates of 0.5–77%/yr as their outcome. A dependency that only exists
   in cells doubling every 24 hours is not obviously a dependency in a tumour doubling over
   years. This is not a confound to regress out; it is a mismatch between what the assay
   measures and what the disease is.

### 6d. The deeper problem: NF2 status is a weak proxy for the biology

Three independent lines of evidence say the subgroup label itself is noisy:

- Yang 2021 (PMID 33805359): *NF2* alteration lowers merlin but is **not associated with
  altered phospho-YAP**; NF2-altered and canonically-Hippo-altered mesotheliomas are
  distinct subsets, and NF2 loss engages Hippo-**independent** signalling.
- The VT3989 phase 1/2 (PMID 41111090): clinical benefit occurred in patients **with and
  without** *NF2* mutations.
- Synodos for NF2 (PMID 29897904): across isogenic schwannoma and meningioma systems,
  **merlin status did not significantly influence drug response**.

This reframes `out/NF2_FINDINGS.md`. That run lists four candidate causes for the failed
positive control — subgroup under-called, subgroup too small, lineage confound, wrong
statistic. A fifth belongs on the list and is arguably first: **the contrast may be
correctly computed and the positive control may simply be a weaker prior than
`../nf2.md` §5 Stage 6 asserts.** "If the calibrated ranking does not recover the Hippo
axis, the pipeline is broken" is too strong a claim given §6d. The honest version is that
failure to recover the axis is *evidence about* the pipeline, weighted by how good the prior
actually is — and the prior is good in schwannoma GEMMs (Laraba) and mediocre in an
NF2-mutation-defined cancer-cell-line panel (Yang, VT3989, Synodos).

### 6e. Verdict — is the disease framing honest?

**No, not as currently written. Yes, if narrowed as follows.**

What the project is actually doing: **selective-dependency ranking in an NF2-mutation-defined
subgroup of a malignant cancer cell line panel.** That is a legitimate object of study, it is
the right shape for the four-question test, and — critically — it is a perfectly good
**methodological** testbed, because the statistical claim (heterogeneous $n$ breaks top-$k$
comparability) does not depend on the biology being transferable at all.

What it is not doing, and must stop implying: producing a shortlist for **NF2-related
schwannomatosis**. There are zero schwannoma lines in the data; no TEAD inhibitor is in a
registered NF2-SWN trial; the one in-lineage genome-wide screen produced hits that do not
appear in the mesothelioma literature; and merlin status does not predict drug response in
the disease's own cell systems.

Three concrete changes this implies for the repository, offered as findings rather than
edits (this lane's brief is to write one file):

1. **`../nf2.md` §4 and §5 should say "NF2-loss cancers, chiefly mesothelioma" wherever they
   currently imply the germline syndrome.** The Stage 0 argument in §4 — score selectivity
   because a lifelong benign condition cannot tolerate a toxic pan-essential target — is
   rhetorically excellent and **does not apply to the population actually in the matrix**,
   which is metastatic cancer. It is the right argument attached to the wrong dataset.
2. **`../state-of-the-art.md` §2 is correct but should name the context split.** The Hippo
   bet is being placed in mesothelioma. The positive control is well chosen for that. The
   claim that it is "the axis with a phase III behind it" should say **which disease** that
   phase III is in ⚠️ — and note that the phase III itself is press-release-only as of
   2026-08-26, with no NCT number.
3. **`out/NF2_FINDINGS.md` should add §6d's cause to its candidate list**, and soften
   `../nf2.md` §5's "the pipeline is broken" to a weighted-prior statement.

None of this kills the project. It changes what the project may claim. A methods paper about
top-$k$ inflation under heterogeneous $n$, demonstrated on an NF2-null DepMap contrast with
an honestly-weighted Hippo prior, is defensible. A shortlist of drug targets for a benign
hereditary hearing-loss syndrome, derived from mesothelioma and lung cancer cell lines, is
not — and the gap between those two sentences is the whole of this lane's finding.

---

## 7. Sources

**Nomenclature and clinical background**

- [Plotkin SR et al., Updated diagnostic criteria and nomenclature for NF2 and schwannomatosis, *Genet Med* 2022;24(9):1967–1977](https://doi.org/10.1016/j.gim.2022.05.007) · [PubMed 35674741](https://pubmed.ncbi.nlm.nih.gov/35674741/)
- [Tamura R, Yo M, Toda M, Historical Development of Diagnostic Criteria for NF2-related Schwannomatosis, *Neurol Med Chir* 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11374461/)
- [GeneReviews — NF2-Related Schwannomatosis (NBK1201)](https://www.ncbi.nlm.nih.gov/books/NBK1201/)

**Merlin biology**

- [Yin F et al., *Cell* 2013;154(6):1342–55](https://doi.org/10.1016/j.cell.2013.08.025) · [Zhang N et al., *Dev Cell* 2010;19(1):27–38](https://doi.org/10.1016/j.devcel.2010.06.015)
- [Li W et al., *Cell* 2010;140(4):477–90](https://doi.org/10.1016/j.cell.2010.01.029) · [Li W et al., *Cancer Cell* 2014;26(1):48–60](https://doi.org/10.1016/j.ccr.2014.05.001)
- [James MF et al., *Mol Cell Biol* 2009;29(15):4250–61](https://doi.org/10.1128/MCB.01581-08) · [López-Lago MA et al., *Mol Cell Biol* 2009;29(15):4235–49](https://doi.org/10.1128/MCB.01578-08)
- [Poulikakos PI et al., *Oncogene* 2006;25(44):5960–8](https://doi.org/10.1038/sj.onc.1209587) · [Curto M et al., *J Cell Biol* 2007;177(5):893–903](https://doi.org/10.1083/jcb.200703010)
- [Morrison H et al., *Genes Dev* 2001;15(8):968–80](https://doi.org/10.1101/gad.189601) · [Lallemand D et al., *Genes Dev* 2003;17(9):1090–1100](https://doi.org/10.1101/gad.1054603) · [Kissil JL et al., *J Biol Chem* 2002;277(12):10394–9](https://doi.org/10.1074/jbc.M200083200)
- [Yang H et al., NF2 and canonical Hippo-YAP define distinct mesothelioma subsets, *Cancers* 2021;13(7):1561](https://doi.org/10.3390/cancers13071561)

**Therapeutic landscape**

- [Yap TA et al., YAP/TEAD inhibitor VT3989 in solid tumors: a phase 1/2 trial, *Nat Med* 2025;31(12):4281–4290](https://doi.org/10.1038/s41591-025-04029-3) · [PubMed 41111090](https://pubmed.ncbi.nlm.nih.gov/41111090/)
- [Plotkin SR et al., Hearing improvement after bevacizumab in NF2, *NEJM* 2009;361(4):358–67](https://doi.org/10.1056/NEJMoa0902579) · [Plotkin SR et al., maintenance bevacizumab, *Neuro Oncol* 2023;25(8):1498–1506](https://doi.org/10.1093/neuonc/noad066) · [Lu VM et al., meta-analysis, *J Neurooncol* 2019;144(2):239–248](https://doi.org/10.1007/s11060-019-03234-8)
- [Brigatinib in NF2-SWN, *NEJM* 2024;390(24)](https://doi.org/10.1056/NEJMoa2400985)
- [Karajannis MA et al., everolimus, *Neuro Oncol* 2014;16(2):292–7](https://doi.org/10.1093/neuonc/not150) · [Karajannis MA et al., lapatinib, *Neuro Oncol* 2012;14(9):1163–70](https://doi.org/10.1093/neuonc/nos146)
- [Fennell DA et al., COMMAND — maintenance defactinib, *J Clin Oncol* 2019;37(10):790–8](https://doi.org/10.1200/JCO.2018.79.0543)
- ClinicalTrials.gov: [NCT04665206 VT3989](https://clinicaltrials.gov/study/NCT04665206) · [NCT04374305 INTUITT-NF2](https://clinicaltrials.gov/study/NCT04374305) · [NCT05228015 IK-930](https://clinicaltrials.gov/study/NCT05228015) · [NCT04857372 IAG933](https://clinicaltrials.gov/study/NCT04857372) · [NCT06251310 SW-682](https://clinicaltrials.gov/study/NCT06251310) · [NCT06566079 ISM6331](https://clinicaltrials.gov/study/NCT06566079) · [NCT01870609 COMMAND](https://clinicaltrials.gov/study/NCT01870609) · [NCT03079999 aspirin](https://clinicaltrials.gov/study/NCT03079999)

**Resistance and combination**

- [Paul S et al., Hippo–MAPK cooperation drives acquired resistance to TEAD inhibition, *Nat Commun* 2025;16:1743](https://doi.org/10.1038/s41467-025-56634-y)
- [Kulkarni A et al., Resistance mechanisms to TEAD-regulated transcription inhibition, *EMBO Rep* 2024;25(9):3944–3969](https://doi.org/10.1038/s44319-024-00217-3)
- [Sun Y et al., Therapeutic limitation of TEAD-YAP blockade, *Nat Commun* 2022;13:6744](https://doi.org/10.1038/s41467-022-34559-0)
- [Akao K et al., TEAD-independent growth via MYC, *Mol Cancer Ther* 2025;24(5):709–719](https://doi.org/10.1158/1535-7163.MCT-24-0308)
- [Chapeau EA et al., IAG933, *Nat Cancer* 2024;5(7):1102–1120](https://doi.org/10.1038/s43018-024-00754-9) · [Hagenbeek TJ et al., GNE-7883, *Nat Cancer* 2023;4(6):812–828](https://doi.org/10.1038/s43018-023-00577-0)
- [Evsen L et al., TEAD-inhibitor drug-combination profiling in Hippo-deficient mesothelioma, *Pharmaceuticals* 2023;16(12):1635](https://doi.org/10.3390/ph16121635)
- [Edwards AC et al., TEAD inhibition overcomes KRAS G12C resistance, *Cancer Res* 2023;83(24):4112–4129](https://doi.org/10.1158/0008-5472.CAN-23-2994) · [Kurppa KJ et al., *Cancer Cell* 2020;37(1):104–122.e12](https://doi.org/10.1016/j.ccell.2019.12.006) · [Pfeifer M et al., *Commun Biol* 2024;7:497](https://doi.org/10.1038/s42003-024-06190-w)
- [Gemma C et al., VGLL1 coactivator switching, *Cancer Res* 2024;84(24):4283–4297](https://doi.org/10.1158/0008-5472.CAN-24-0013) · [Ott CA et al., TAZ-TEAD in minimal residual disease, *Nat Commun* 2025;16:9655](https://doi.org/10.1038/s41467-025-64682-7)
- [Benton D et al., PAK + Hippo inhibitor synergy in NF2-deficient schwannoma, *PLoS One* 2024;19(7):e0305121](https://doi.org/10.1371/journal.pone.0305121)

**Dependencies and screens**

- [Kyrkou A et al., G6PD and ACSL3 are synthetic lethal partners of NF2 in Schwann cells, *Nat Commun* 2024;15(1):5115](https://doi.org/10.1038/s41467-024-49298-7) · [PMC11180199](https://pmc.ncbi.nlm.nih.gov/articles/PMC11180199/)
- [Laraba L et al., Inhibition of YAP/TAZ-driven TEAD activity prevents growth of NF2-null schwannoma and meningioma, *Brain* 2023;146(4):1697–1713](https://doi.org/10.1093/brain/awac342)
- [Xu D et al., De novo pyrimidine synthesis in NF2-deficient mesothelioma, *EMBO Mol Med* 2025;17(9):2258–2298](https://doi.org/10.1038/s44321-025-00278-4)
- [White SM et al., YAP/TAZ inhibition induces targetable vulnerabilities in NF2-deficient tumor cells, *Dev Cell* 2019;49(3):425–443.e9](https://doi.org/10.1016/j.devcel.2019.04.014)
- [Licciulli S et al., FRAX597 in NF2-associated schwannoma, *J Biol Chem* 2013;288(40):29105–14](https://doi.org/10.1074/jbc.M113.510933)
- [Klingbeil O et al., MARK2/MARK3 codependencies of YAP/TAZ, *Cancer Discov* 2024;14(12):2471–2488](https://doi.org/10.1158/2159-8290.CD-23-1529)
- [Shapiro IM et al., Merlin deficiency predicts FAK inhibitor sensitivity, *Sci Transl Med* 2014;6(237):237ra68](https://doi.org/10.1126/scitranslmed.3008639)
- [McDonald ER 3rd et al., Project DRIVE, *Cell* 2017;170(3):577–592.e10](https://doi.org/10.1016/j.cell.2017.07.005)
- [Synodos for NF2 Consortium, *PLoS One* 2018;13(6):e0197350](https://doi.org/10.1371/journal.pone.0197350)
