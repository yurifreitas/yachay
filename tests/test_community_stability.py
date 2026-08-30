"""The clustering tool's determinism, on a graph small enough to test.

WHY A SEPARATE FILE. `tests/test_determinism.py` reruns a tool and compares the artefact's
digest, which is the right test and takes 161 seconds here — three algorithms twelve times
each, a resolution sweep and twelve rewirings over 5,524 nodes. So that suite excludes this
tool by name, with a reason, and the property it would have checked is checked here instead on
a graph built for the purpose.

WHAT IS ACTUALLY AT RISK. Every partitioner in the tool takes a seed, and two of them come
from libraries this repository had never used. A seed that does not fix the answer would make
the stability measurement meaningless in the most confusing possible way: the artefact would
report disagreement between seeds that is really disagreement between runs, and no number in
it would mean what it says.
"""

from __future__ import annotations

import importlib.util
import pathlib

import networkx as nx
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load():
    spec = importlib.util.spec_from_file_location(
        "community_stability", ROOT / "tools" / "community_stability.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ImportError as exc:  # pragma: no cover - environment without the clustering deps
        pytest.skip(f"clustering dependencies absent: {exc}")
    return mod


@pytest.fixture(scope="module")
def graph():
    """Four planted cliques joined by single edges — a graph with an unarguable answer.

    Deliberately not a random graph. If the partitioners disagree on THIS, the disagreement is
    in the code rather than in the data, and the test would be measuring the wrong thing.
    """
    g = nx.Graph()
    for c in range(4):
        base = c * 12
        for i in range(12):
            for j in range(i + 1, 12):
                g.add_edge(base + i, base + j)
    for c in range(3):
        g.add_edge(c * 12, (c + 1) * 12 + 1)
    return g


def test_a_seed_fixes_every_partitioner(graph):
    mod = load()
    a = mod.run_algorithms(graph, seed=7)
    b = mod.run_algorithms(graph, seed=7)
    for name in a:
        assert (a[name] == b[name]).all(), f"{name} is not reproducible at a fixed seed"


def test_the_partitioners_find_the_planted_cliques(graph):
    """A stability number is only meaningful if the method can find structure that is there."""
    mod = load()
    labs = mod.run_algorithms(graph, seed=7)
    for name in ("louvain", "leiden"):
        assert len(set(labs[name].tolist())) == 4, f"{name} did not recover four cliques"


def test_disconnected_communities_are_detected(graph):
    """The check for the defect Leiden exists to prevent must be able to fire.

    A detector that has never returned a non-zero count is a detector nobody has tested, and
    this repository has shipped one of those before — a regex that could never match.
    """
    mod = load()
    honest = mod.run_algorithms(graph, seed=7)["leiden"]
    assert mod.internally_disconnected(graph, honest)["communities"] == 0

    # Now a partition that IS broken: put one clique's members in with a distant clique's.
    broken = honest.copy()
    broken[36:] = broken[0]
    found = mod.internally_disconnected(graph, broken)
    assert found["communities"] == 1, found
    assert found["pieces_they_split_into"] == 2, found


def test_consensus_confidence_is_bounded_and_singletons_are_not_scored(graph):
    mod = load()
    g = graph.copy()
    g.add_node(999)  # an isolated gene, like the 2,189 in the real graph
    runs = [mod.run_algorithms(g, seed=s)["leiden"] for s in (1, 2, 3)]
    _, conf = mod.consensus(runs, g, seed=7)
    import numpy as np

    scored = conf[~np.isnan(conf)]
    assert scored.size, "nothing was scored"
    assert scored.min() >= 0.0 and scored.max() <= 1.0
    # The isolated node must be unscored rather than perfectly confident: scoring it 1.0 is
    # how the headline number would gain forty points from genes with no edges at all.
    assert np.isnan(conf[list(g.nodes()).index(999)])
