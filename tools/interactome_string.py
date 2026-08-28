#!/usr/bin/env python
"""The falsifier: is our modularity result biology, or is it how HPO was curated?

WHAT THIS EXISTS TO ATTACK. `tools/interactome_sparse.py` measured the HPO gene-disease
graph and reported **modularity 0.861 against 0.162** for a degree-matched rewiring, and
`docs/references/rare-disease-mechanisms.md` §2 used that number as an independent
observation of the disease-module structure Menche et al. describe. §5.2 of the same
document then named the obvious objection and called it **the weakest claim in the
document**:

    "If the modularity excess survives on a graph with the biology removed but the
     ANNOTATION PROCESS preserved, then §2 is measuring how HPO was curated, not how
     biology is organised. The degree-matched null does not rule this out."

The objection is not academic. Our graph joins two genes when they cause a common disease,
so **a disease with k genes contributes a k-clique by construction**. Cliques are the most
modular object there is. A large part of that 0.861 could be the shape of the annotation
rather than the shape of the cell, and a degree-matched rewiring cannot tell the difference
because it destroys the cliques along with everything else.

THE TEST. STRING is an independent human interaction network whose edges come from an
entirely different evidence base - experiments, curated complexes, co-expression, text
mining - and which is not built by joining things that share a disease label. If the
modularity excess is a property of biological networks, STRING shows it too. If it is a
property of how HPO records diseases, STRING does not.

WHAT IS AND IS NOT COMPARABLE. Absolute modularity is NOT comparable across graphs: it
depends on size and density, and STRING is far denser than ours. The comparable quantity is
the **excess over each graph's own degree-matched null**, computed with the same method
(Louvain, same seed) on both sides. That is what this file reports, and any reading of the
raw modularity across the two graphs is wrong.

    python tools/interactome_string.py               # score >= 700, the standard cut
    python tools/interactome_string.py --score 900   # and the robustness check

The result is allowed to come back against us. That is the point of running it.
"""

from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import sys

import networkx as nx
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

OUT = ROOT / "out"
# The same seed the HPO run uses. Louvain is stochastic; comparing two graphs under
# different seeds would put noise exactly where the finding is supposed to be.
SEED = 20260827


def load_string(min_score: int) -> nx.Graph:
    """Human protein links above a confidence threshold, as a simple undirected graph.

    STRING lists every pair twice (a->b and b->a). `nx.Graph` collapses them, so no
    de-duplication is needed - but the edge count printed by this file is the collapsed one
    and is half what a line count of the source would suggest.
    """
    g = nx.Graph()
    path = BY_KEY["string_links"].dest
    with gzip.open(path, "rt") as fh:
        next(fh)                                  # header
        for line in fh:
            a, b, score = line.rstrip("\n").split(" ")
            if int(score) >= min_score:
                g.add_edge(a, b)
    return g


def degree_matched_null(g: nx.Graph, rng: np.random.Generator) -> nx.Graph:
    """The same null the HPO run uses: configuration model, collapsed, self-loops removed.

    Collapsing parallel edges loses a little of the degree sequence, which is why the null's
    edge count comes out slightly below the real graph's. That is a property of the method
    rather than of this file, and it is reported rather than corrected so the two runs stay
    comparable.
    """
    deg_seq = [d for _, d in g.degree()]
    null_multi = nx.configuration_model(deg_seq, seed=int(rng.integers(1 << 30)))
    null = nx.Graph(null_multi)
    null.remove_edges_from(nx.selfloop_edges(null))
    return null


def characterise(g: nx.Graph, label: str) -> dict:
    comms = nx.community.louvain_communities(g, seed=SEED)
    mod = nx.community.modularity(g, comms)
    sizes = sorted((len(c) for c in comms), reverse=True)
    return {
        "label": label,
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "modularity": round(float(mod), 4),
        "communities": len(comms),
        "largestCommunity": sizes[0] if sizes else 0,
        "medianCommunity": sizes[len(sizes) // 2] if sizes else 0,
        "meanDegree": round(2 * g.number_of_edges() / max(g.number_of_nodes(), 1), 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", type=int, default=700,
                    help="STRING combined_score floor (700 = high confidence)")
    args = ap.parse_args()

    path = BY_KEY["string_links"].dest
    if not path.exists():
        raise SystemExit("missing %s — run python tools/ingest.py" % path.name)

    rng = np.random.default_rng(SEED)

    print("loading STRING at score >= %d ..." % args.score)
    real = load_string(args.score)
    print("  %s nodes, %s edges" % (f"{real.number_of_nodes():,}",
                                    f"{real.number_of_edges():,}"))

    print("communities on the real graph ...")
    res_real = characterise(real, "STRING, real")
    print("communities on the degree-matched null ...")
    res_null = characterise(degree_matched_null(real, rng), "STRING, degree-matched")

    string_excess = round(res_real["modularity"] - res_null["modularity"], 4)
    string_ratio = (round(res_real["modularity"] / res_null["modularity"], 2)
                    if res_null["modularity"] else None)

    # ---- our own result, read rather than restated -------------------------------------
    ours = None
    hpo_path = OUT / "interactome_sparse.json"
    if hpo_path.exists():
        h = json.loads(hpo_path.read_text(encoding="utf-8"))
        # Nested under `structure`, not at the top level. The first version of this reader
        # looked in the wrong place and reported "nothing to compare against" — a comparison
        # that silently finds no comparand is the quiet failure mode this whole file is
        # about, so it is worth the two lines to say where the number actually lives.
        real_mod = h.get("real", {}).get("structure", {}).get("modularity")
        null_mod = h.get("null", {}).get("structure", {}).get("modularity")
        if real_mod is not None and null_mod is not None:
            ours = {
                "graph": "HPO gene-disease co-occurrence",
                "modularity": real_mod,
                "nullModularity": null_mod,
                "excess": round(real_mod - null_mod, 4),
                "ratio": round(real_mod / null_mod, 2) if null_mod else None,
                "construction": ("two genes are joined when they cause a common disease, so "
                                 "a disease with k genes contributes a k-CLIQUE. The "
                                 "construction itself is highly modular."),
            }

    # ---- the verdict, written to be readable against us --------------------------------
    if ours:
        survives = string_excess >= 0.5 * ours["excess"]
        verdict = "survives" if survives else "does not survive"
        says = (
            "STRING shows a modularity excess of %.4f over its own degree-matched null "
            "(%.4f vs %.4f). Ours is %.4f. The claim in rare-disease-mechanisms.md §2 %s "
            "the independent graph."
            % (string_excess, res_real["modularity"], res_null["modularity"],
               ours["excess"], verdict)
        )
    else:
        survives, verdict = None, "not comparable"
        says = ("out/interactome_sparse.json is missing, so there is nothing to compare "
                "against. Run the HPO interactome stage first.")

    payload = {
        "generated": "tools/interactome_string.py",
        "input": str(path.relative_to(ROOT)).replace("\\", "/"),
        "scoreFloor": args.score,
        "premise": (
            "rare-disease-mechanisms.md §5.2 names our modularity result as the weakest "
            "claim in the document and states the null that would falsify it: an "
            "independent graph, built without joining things that share a disease label."
        ),
        "comparability": (
            "Absolute modularity is NOT comparable across graphs of different size and "
            "density. Only the EXCESS over each graph's own degree-matched null is, and "
            "both sides use the same method and seed."
        ),
        "string": {"real": res_real, "null": res_null,
                   "excess": string_excess, "ratio": string_ratio},
        "hpo": ours,
        "survives": survives,
        "verdict": verdict,
        "says": says,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"interactome_string_{args.score}.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("  %-34s modularity %.4f  (%d communities)"
          % ("STRING, real", res_real["modularity"], res_real["communities"]))
    print("  %-34s modularity %.4f  (%d communities)"
          % ("STRING, degree-matched null", res_null["modularity"], res_null["communities"]))
    print("  %-34s %.4f" % ("STRING excess", string_excess))
    if ours:
        print("  %-34s %.4f  (%.4f vs %.4f)"
              % ("HPO excess, ours", ours["excess"], ours["modularity"],
                 ours["nullModularity"]))
    print()
    print("  VERDICT: %s" % says)
    print("wrote %s" % dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
