#!/usr/bin/env python
"""The author's own constructs, each with the falsifier he wrote for it.

WHY THIS FILE IS A SEED AND NOT A MEASUREMENT. It encodes five theories recovered from Yuri
Freitas' own notes on what he calls symbiotic mathematics, in the four-block form he asked for
them: the statement in his notation, the nearest published precedent, what public data would
test it, and what numerical result would kill it. Two of the five are now measured by tools in
this repository; the rest are not, and the difference is the point of publishing the list.

THE HONEST PART IS THE STATUS FIELD. A framework that presents its untested parts in the same
voice as its tested ones is advertising. Here each construct carries one of:

    measured                a tool computes it, against a null, with an interval
    testable_not_yet_run    the data exists and the statistic is specified
    no_public_falsifier     no dataset listed can kill it — usually because a term in the
                            statement has no operational definition

The third is not a criticism smuggled in. It is his own verdict on his own work, recorded in
the notes: "sem isso, ρ_S pode ser ajustado retrospectivamente para explicar qualquer coisa."
A theory that survives because it cannot be tested has not survived anything.

    python tools/methods_seed.py

Stdlib only.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare" / "methods.json"

METHODS = [
    {
        "id": "relational_primacy",
        "name": "Campo Simbiótico Não-Originário",
        "subtitle": "configuration, not generation",
        "status": "measured",
        "measured_by": "tools/relational_primacy.py",
        "statement": (
            "Reality is not generated, it is configured; the observable is a local "
            "stabilisation of relations inside a wider field of possibility. "
            "Object ∉ Fundamental; Relations + Constraints → Stable Configurations → "
            "Observed Objects. The biomedical form: entities should be more predictable from "
            "their RELATIONS than from their intrinsic attributes in isolation."),
        "precedent": (
            "Ontic structural realism — Ladyman, Ross, Spurrett & Collier, Every Thing Must "
            "Go, OUP 2007, DOI 10.1093/acprof:oso/9780199276196.003.0003. Rovelli, Relational "
            "Quantum Mechanics, Int. J. Theor. Phys. 35, 1637 (1996), DOI 10.1007/BF02302261."),
        "what_is_his": (
            "Not 'properties are relational', which is the precedent. His addition is "
            "possibility → tension → stabilisation, and replacing origin with configuration "
            "ontologically. That addition is metaphysics and is not what was tested."),
        "measurement": (
            "HPO gene–disease, with the eleven-feature attribute space this site publishes. "
            "Both arms get the same seed genes: one scores attribute resemblance to the seed "
            "centroid, the other scores random-walk reach. Leave-one-disease-out. AUPRC on "
            "held-out genes, degree-preserving rewiring as control."),
        "falsifier": (
            "Seriously weakened if ΔAUPRC ≤ 0 consistently, or if relations add less than "
            "0.01 with a 95% interval containing zero."),
        "result": (
            "ΔAUPRC = +0.287 [+0.239, +0.339] over 155 diseases; relational wins in 83.9% of "
            "them and beats a degree-matched rewiring by +0.297. The falsifier does not "
            "trigger."),
    },
    {
        "id": "nonreciprocal",
        "name": "Relação assimétrica como geradora de organização",
        "subtitle": "r_ij ≠ r_ji",
        "status": "measured",
        "measured_by": "tools/nonreciprocal.py",
        "statement": (
            "A relation need not be reciprocal: A may attract B while B repels A. The claim "
            "is that NON-RECIPROCITY generates organisation, not merely that interaction "
            "does. The operator is the system against its own symmetric projection, "
            "Δ_sym = Q(R) − Q((R + Rᵀ)/2)."),
        "precedent": (
            "Ivlev et al., Statistical Mechanics where Newton's Third Law is Broken, Phys. "
            "Rev. X 5 011035 (2015), DOI 10.1103/PhysRevX.5.011035. Schmickl, Stefanec & "
            "Crailsheim, Sci. Rep. 6 37969 (2016), DOI 10.1038/srep37969."),
        "what_is_his": (
            "That asymmetry produces emergent behaviour is not new. What may be his is using "
            "the difference between a system and its OWN symmetric projection as a "
            "quantitative operator for discovering organisation."),
        "measurement": (
            "Asymmetric affinity w(i→j) = |D_i ∩ D_j| / |D_i| on HPO gene–disease, against "
            "its symmetric projection, judged on recovering held-out disease genes by AUPRC. "
            "Leave-one-disease-out. Control: randomise the direction of the antisymmetric "
            "part while preserving its magnitude exactly."),
        "falsifier": (
            "Dies if E[S_NR] ≤ 0 with a 95% interval containing zero; strictly, if "
            "|S_NR| < 0.01 in ≥80% of diseases and no benefit survives permutation controls."),
        "result": (
            "S_NR = +0.0605 [+0.0475, +0.0757] over 246 diseases, positive in 69.1%. "
            "Randomising the direction gives −0.0034 — a wrong direction is worth nothing, "
            "the true one is worth something. Neither form of the falsifier triggers."),
    },
    {
        "id": "symbolic_density",
        "name": "Densidade Simbólica",
        "subtitle": "meaning as a dynamic density, not a label",
        "status": "testable_not_yet_run",
        "measured_by": None,
        "statement": (
            "ρ_S = (αI + βM + γU + δE) / (Δt Δx ΔI) — intention, memory, mutation and "
            "expression per unit of time, space and information. The interesting part is not "
            "the sum: it is treating meaning as a local dynamic density rather than an "
            "external semantic label."),
        "precedent": (
            "Kolchinsky & Wolpert, Semantic information, autonomous agency and non-equilibrium "
            "statistical physics, Interface Focus 8, 20180041 (2018), DOI "
            "10.1098/rsfs.2018.0041 — semantic information as that causally necessary for a "
            "system to maintain its existence. Krakauer et al., The information theory of "
            "individuality, Theory Biosci. 139, 209 (2020), DOI 10.1007/s12064-020-00313-7."),
        "what_is_his": (
            "Mixing memory, mutation, expression and meaning into one local dynamic quantity. "
            "No equivalent published definition was found."),
        "measurement": (
            "Drop 'intention', which has no operational definition, and test "
            "ρ*_S = I(X_past; X_future) + I(G; E) + I(perturbation; response) on GEO "
            "time-course and perturbation series, PRIDE proteomics, Reactome and the Human "
            "Protein Atlas. ρ should predict functional preservation after perturbation."),
        "falsifier": (
            "Dies if ρ*_S carries no predictive information about post-perturbation "
            "preservation beyond expression level and degree."),
        "result": None,
        "blocked_on": (
            "GEO time-course and PRIDE are not ingested here. The statistic is specified and "
            "the data is public; nothing about it is measured yet, and saying so is the "
            "difference between a research plan and a claim."),
    },
    {
        "id": "symbiotic_collapse",
        "name": "Colapso Simbiótico",
        "subtitle": "intention → vibration → form → entanglement",
        "status": "no_public_falsifier",
        "measured_by": None,
        "statement": (
            "P(X_{t+1} | X_t) replaced by P(X_{t+1} | X_t, C_t, M_t): the realised "
            "configuration is selected by state, context and history rather than by a fixed "
            "Markov rule. Possibilities are configured, not merely drawn."),
        "precedent": (
            "Non-Markovian dynamics and coarse-graining with memory — Li, Bian, Li & "
            "Karniadakis, Incorporation of memory effects in coarse-grained modeling via the "
            "Mori–Zwanzig formalism, J. Chem. Phys. 143, 243128 (2015), DOI "
            "10.1063/1.4935490."),
        "what_is_his": (
            "The ontological reading: memory + context → selection of the realised "
            "configuration. There is no clear scientific precedent for calling that "
            "'collapse'."),
        "measurement": (
            "The memory/context half IS testable: GEO experiments with the same perturbation "
            "and different histories, comparing X_{t+1} = f(X_t) against "
            "X_{t+1} = f(X_t, …, X_{t−k}) by out-of-sample ΔR² or Δlog-likelihood."),
        "falsifier": (
            "The memory half dies if ΔR² ≤ 0 systematically, or if AIC prefers the Markov "
            "model after regularisation. ⚠️ The 'intention causes collapse' half has NO public "
            "falsifier, because intention has no operational definition."),
        "result": None,
        "blocked_on": (
            "Half of this construct cannot be killed by any public dataset. That is recorded "
            "here rather than left for a reader to discover, because a claim that cannot fail "
            "is not evidence, however well it reads."),
    },
    {
        "id": "morphogenetic_field",
        "name": "Campo Morfogenético com memória ativa",
        "subtitle": "SpectralMorphoEngine",
        "status": "testable_not_yet_run",
        "measured_by": None,
        "statement": (
            "Fields A(x,y,t), B(x,y,t), V_mem(x,y,t), Light(x,y,t) on a 4096-resolution "
            "lattice with random spatial seeds and noise B₀ ← B₀ + ε, ε ~ N(0, 0.04²). "
            "Reaction–diffusion with a five-point Laplacian and an AB² nonlinearity, "
            "parameters D_a, D_i, f, k plus conductance and optical sensitivity — a "
            "Gray–Scott system carrying an ACTIVE MEMORY field, which is the part that is not "
            "standard."),
        "precedent": (
            "Gray–Scott reaction–diffusion, and Turing, The chemical basis of morphogenesis, "
            "Phil. Trans. R. Soc. B 237, 37 (1952), DOI 10.1098/rstb.1952.0012. Memory fields "
            "coupled to reaction–diffusion are studied, but the specific coupling here — "
            "conductance and optical sensitivity modulating the memory field — was not found "
            "as a published system."),
        "what_is_his": (
            "The concrete implementation exists as his own code. The claim needing a test is "
            "that the memory field changes which patterns are REACHABLE, not merely how fast "
            "they form."),
        "measurement": (
            "Self-contained and needs no external dataset: sweep the parameter plane with the "
            "memory field on and off, and compare the set of terminal pattern classes. "
            "Statistic: the share of (f, k) cells whose terminal class differs, against a "
            "null where the memory field is present but decoupled."),
        "falsifier": (
            "Dies if the terminal pattern class is unchanged by the memory field across the "
            "parameter plane — that is, if memory changes only transients."),
        "result": None,
        "blocked_on": (
            "Nothing external. This is the one construct here that could be tested today "
            "without ingesting anything, and it is not implemented in this repository yet."),
    },
]


def main() -> int:
    payload = {
        "generated": "tools/methods_seed.py",
        "governed_by": "docs/adr/0007 — a construct enters when a tool computes it with a "
                       "null and an interval",
        "whose": (
            "Yuri Freitas' own constructs, recovered from his notes and encoded in the "
            "four-block form he asked for: statement, precedent, measurement, falsifier."),
        "why_the_status_field": (
            "A framework that presents its untested parts in the same voice as its tested "
            "ones is advertising. Two of these five are measured against a null with an "
            "interval; two are specified but not run; one has a half that no public dataset "
            "can kill, which is his own verdict on it, not a criticism added here."),
        "counts": {
            "total": len(METHODS),
            "measured": sum(1 for m in METHODS if m["status"] == "measured"),
            "testable_not_yet_run": sum(1 for m in METHODS
                                        if m["status"] == "testable_not_yet_run"),
            "no_public_falsifier": sum(1 for m in METHODS
                                       if m["status"] == "no_public_falsifier"),
        },
        "methods": METHODS,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  {len(METHODS)} constructs: "
          f"{payload['counts']['measured']} measured, "
          f"{payload['counts']['testable_not_yet_run']} specified but not run, "
          f"{payload['counts']['no_public_falsifier']} with no public falsifier")
    print(f"wrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
