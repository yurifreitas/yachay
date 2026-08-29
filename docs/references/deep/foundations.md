# The mid-century foundations, and what each one is doing here

> **Role:** explanation. The pre-1970 work that the approaches in
> [`../theory-atlas.md`](../theory-atlas.md) descend from — Turing, Shannon, von Neumann,
> Ashby, Wiener, Waddington, Kolmogorov — with, for each, **the specific measurement or
> specific open problem in this repository that it bears on**. A name with no such tie is not
> in this file.
> **Last revised:** 2026-08-29 · **State:** eight foundations, three of them attached to a
> number measured here and two of those tested against their own prediction. The rest carry
> an open problem instead, and say so.
>
> **Verification.** Every citation below was resolved through the Crossref API on 2026-08-29 —
> title, authors, venue, year, DOI. None was typed from memory. Where a work exists mainly as
> a book or a reprint volume, the DOI is that edition's and is marked.
>
> **Why this file has a rule.** A repository like this one attracts genealogy: it is pleasant
> to write that a measurement descends from Turing. ADR 0007 forbids a formalism entering
> without a number, and the same discipline is applied here to a name. **Two of these
> foundations made a prediction that was tested on this project's data. One of them failed.**
> That is the point of the file.

---

## 1. Turing 1952 — form is not a list of reactions

`[XR]` **A. M. Turing, "The chemical basis of morphogenesis", Philosophical Transactions of
the Royal Society B 237:37–72, 1952. DOI `10.1098/rstb.1952.0012`.**

**The claim.** Two substances that react and diffuse at different rates can spontaneously
break symmetry and produce a stable spatial pattern. A structure — where something is, how
often it repeats, on what scale — can arise from a mechanism that names no structure. The
mathematics is a field over space and time, `∂u/∂t = D∇²u + R(u)`, not an inventory of
reactions.

**What it bears on here, and it was tested.** `tools/scale_information.py` measures how much
of what a disease's causal genes say about its organ systems survives being collapsed onto
Reactome top-level pathways. A pathway is an inventory of reactions. Turing's argument says
that vocabulary should be adequate where the abnormality is a *process running wrongly* and
inadequate where it is a *structure that formed wrongly*, because the pathway alphabet has no
words for where and when.

The twenty organ systems were split accordingly — morphogenetic against physiological — and
the retentions grouped:

| class | systems | mean pathway retention |
|---|---:|---:|
| physiological (metabolism, blood, immune, endocrine, neoplasm, cellular phenotype) | 6 | **0.238** |
| morphogenetic (eye, limbs, ear, head/neck, musculoskeletal, integument, prenatal, cardiovascular, respiratory, digestive, genitourinary, growth, nervous, breast) | 14 | **0.138** |
| difference | | **+0.099**, permutation p = **0.0185** (20,000 draws, one-sided) |

**The caveat, which is not optional.** The per-system retentions were already printed when the
classification was written. This is therefore a *description with a p-value*, not a
pre-registered test — the distinction ADR 0006 draws for thresholds, applied to a
classification. What protects it from circularity is that the split follows the two
literatures rather than the ranking, that it was not revised after the test ran, and that the
two genuinely ambiguous systems (nervous, cardiovascular — each a structure that forms and
then a process that runs) were assigned to the class that makes the test *harder* to pass.
Promoting it to a real test needs a second, unlooked-at ontology; MONDO's disease classes are
the obvious candidate and nobody here has opened them.

**What it does not show.** Not that Turing's mechanism operates in these diseases. That would
need dynamics, and §5 of [`multiscale-formalism.md`](multiscale-formalism.md) records that
this project has none. It shows that the alphabet which describes processes loses more signal
exactly where the theory says form is what fails.

---

## 2. Von Neumann 1956 — reliability out of unreliable parts, and where it fails

`[XR]` **J. von Neumann, "Probabilistic logics and the synthesis of reliable organisms from
unreliable components", in *Automata Studies* (AM-34), 1956. DOI
`10.1515/9781400882618-003`.** `[XR]` Later development: N. Pippenger, Proc. Symp. Pure Math.
50, 1990, DOI `10.1090/pspum/050/1067764`.

**The claim.** An arbitrarily reliable computation can be built from unreliable elements by
*multiplexing* — replicate the element, take a majority, and the error rate falls with
redundancy.

**What it bears on here, and it was tested — and the prediction failed.** ClinVar is that
construction running in public: each submitter is an unreliable element, the archive
aggregates them, a clinician consumes the aggregate. `tools/conflict_decomposition.py` holds
the context fixed — one variant, one condition — and asks how internal disagreement moves as
submitters are added:

| submitters | (variant, condition) pairs | internally split | 95% CI |
|---|---:|---:|---|
| 2 | 188,006 | **17.9%** | [17.8, 18.1] |
| 3 | 42,079 | 25.4% | [25.0, 25.8] |
| 4 | 13,385 | 24.7% | [24.0, 25.5] |
| 5 | 5,718 | 24.3% | [23.2, 25.4] |
| 6–10 | 6,512 | 23.7% | [22.7, 24.7] |
| 11+ | 1,206 | 20.6% | [18.5, 23.0] |

**Disagreement does not fall with redundancy. It rises, then holds near a quarter.** Adding
submitters past the second reveals variety rather than absorbing it, and it keeps revealing it
at eleven submitters as readily as at three.

**This is not a criticism of ClinVar** — an archive that *records* rather than adjudicates
should look exactly like this, and the rise from 2 to 3 is partly the arithmetic of a third
opinion being able to disagree at all. But it settles a design question for anything built on
top: **an aggregate classification is not a consensus, and depth of review does not make it
one.** The residual ~24% is a property of the corpus, not a transient to be waited out.

---

## 3. Ashby 1956 — only variety can absorb variety

`[XR]` **W. R. Ashby, *An Introduction to Cybernetics*, 1956. DOI `10.5962/bhl.title.5851`.**
`[XR]` The law restated: "Requisite Variety and Its Implications for the Control of Complex
Systems", in *Facets of Systems Science*, 1991, DOI `10.1007/978-1-4899-0718-9_28`.

**The claim.** A regulator can only absorb as much variety as it itself possesses. Reduce the
regulator's variety below the disturbance's and control fails, necessarily, for reasons of
counting rather than of engineering.

**What it bears on here.** Read "regulator" as "representation" and the law becomes the
argument for the strongest engineering conclusion this project has reached: **there is no
single right coarse-graining for the atlas.** The three measurements each found a population
whose variety a single figure cannot carry — retention spanning 5.6-fold across organ systems,
language coverage spanning 100% to zero, conflict that is contradiction in one half of cases
and context in the other. In each, the pooled number is not imprecise; it names something that
does not exist.

Ashby is doing real work here and not decorating: he supplies the reason the finding *had* to
be a gradient rather than a constant, and the reason a per-system choice of scale is
principled rather than an admission of defeat.

**Open, not measured.** The law's quantitative form (`H(outcome) ≥ H(disturbance) − H(regulator)`)
has not been computed for any representation in this project. It could be: the entropies are
the same ones `scale_information.py` already estimates. That is a buildable row nobody has
written.

---

## 4. Shannon 1948 — the currency all of this is paid in

`[XR]` **C. E. Shannon, "A mathematical theory of communication", Bell System Technical
Journal 27:379–423, 1948. DOI `10.1002/j.1538-7305.1948.tb01338.x`.**

Directly instantiated: every headline in `scale_information.json` is a mutual information in
bits, and the whole cross-scale result is the statement that a summary can only lose. Shannon
is not background here; he is the estimator. The bias of that estimator in finite samples
(`[XR]` Paninski 2003, DOI `10.1162/089976603321780272`) is what produced this project's one
recorded estimator failure — a bootstrap interval that did not contain its own point estimate.

---

## 5. Wiener 1948 — the loop as the unit

`[XR]` **N. Wiener, *Cybernetics, or Control and Communication in the Animal and the
Machine*, 2nd edn 1961. DOI `10.1037/13140-000`.**

**What it bears on here: an open problem, honestly.** Wiener's unit is the feedback loop —
system and controller as one object, with the measurement inside the loop rather than outside
it. Every layer in this repository is *outside* the loop: it observes a catalogue and reports.
`tools/twin_propagation.py` moves a perturbation on a graph but nothing feeds back.

The concrete open problem Wiener names is in the atlas as `analogy`: state and topology
co-evolving, `Ẋ = F(X,Γ)` with `Γ̇ = G(Γ,X)`. Its blocker is the same longitudinal data
everything dynamical waits on. Wiener is here as the earliest clear statement of what is
missing, not as an ancestor of anything built.

---

## 6. Waddington 1942 — canalisation, and why severity is the wrong axis

`[XR]` **C. H. Waddington, "Canalization of development and the inheritance of acquired
characters", Nature 150:563–565, 1942. DOI `10.1038/150563a0`.** `[XR]` The landscape made
computational: Wang, Zhang, Xu & Wang, PNAS 108:8257, 2011, DOI `10.1073/pnas.1017017108`.

**The claim.** Development is buffered. A trajectory returns to its channel under perturbation,
and what matters is not where the system is but how deep the channel is around it.

**What it bears on here.** This is the strongest available argument that **severity is
mis-modelled across this whole field**, including in this project's own layers. A severity
grade records where a patient is; canalisation says the clinically decisive quantity is how
much perturbation the state can still absorb — which is the viability kernel of
[`multiscale-formalism.md`](multiscale-formalism.md) §11, and is not measured anywhere here.
Two patients with identical phenotypes and different remaining channel depth are not in the
same condition, and no artefact in `out/rare/` can tell them apart.

---

## 7. Kolmogorov 1965 and Chaitin 1966 — description length as the arbiter

`[XR]` **A. N. Kolmogorov, "Three approaches to the quantitative definition of information",
Int. J. Computer Mathematics 2:157–168, 1968 (translated). DOI `10.1080/00207166808803030`.`**
`[XR]` **G. J. Chaitin, "On the length of programs for computing finite binary sequences",
Journal of the ACM 13:547–569, 1966. DOI `10.1145/321356.321363`.** `[XR]` The operational
form this project would use: Rissanen, "Modeling by shortest data description", Automatica
14:465–471, 1978, DOI `10.1016/0005-1098(78)90005-5`.

**What it bears on here.** The atlas's §3 records competing mechanistic models as something to
display side by side with posterior weights. Description length is the alternative arbiter that
does not need a prior: `L(M) + L(D|M)`, with the complex model paying for its own complexity.
It is also the honest tie-breaker for the cross-scale result — the pathway scale keeps 22% of
the information at 181-fold compression, and whether that trade is *good* is a description-
length question that has not been asked.

**Open, and cheap.** This is a buildable row: both terms are computable from artefacts already
on disk.

---

## 8. Turing 1936 — the limit that applies to the executable-model ambition

`[XR]` **A. M. Turing, "On computable numbers, with an application to the
Entscheidungsproblem", 1936; cited from *The Essential Turing*, 2004, DOI
`10.1093/oso/9780198250791.003.0005`.**

**What it bears on here.** The atlas's ambition includes models that are *executable* —
downloadable, runnable, composable. Turing's result is the reason a general "will this
composed model behave" question has no general answer: non-trivial properties of arbitrary
programs are undecidable, so a composition framework cannot promise to verify what it composes.

This is not an obstacle to building one; it is the reason the framework must demand
**declared interfaces** — units, domain, time scale, uncertainty — rather than attempt to infer
compatibility. Which is exactly what the compositional-systems-biology line in
[`multiscale-formalism.md`](multiscale-formalism.md) §4 argues on independent grounds. Turing
1936 says that requirement is not a convenience; it is the only route available.

---

## 9. What the two tests did to this file

Eight foundations. Two made a prediction that could be checked against data this project
holds, and **the checks disagreed with each other**:

* **Turing's holds.** The alphabet of processes loses more where the theory says form is what
  fails — +0.099, p = 0.0185, with the target-contact caveat stated in full.
* **Von Neumann's does not.** Multiplexing predicts that redundancy buys reliability; in
  ClinVar, internal disagreement rises with the second opinion and then holds near a quarter
  through eleven.

A file of foundations where every ancestor turns out to be right is a file that was written to
flatter its subject. The useful output of this one is the failure: **an aggregate ClinVar
classification cannot be treated as a consensus**, and that follows from a measurement rather
than from a caveat — which is also the reason von Neumann earns his section rather than
decorating it.
