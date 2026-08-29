"""The read-site detector must find the reader of a file that is demonstrably read.

WHY THIS TEST EXISTS, and it is audit finding A37. `tools/status.py` decides whether an
ingested file has ever been *read* by walking each module's AST for a read call whose argument
resolves to a filename. `docs/status.md` publishes the answer, and the answer is wrong: it
reports files as never opened that a shipped tool reads on every run.

The obvious fix was tried on 2026-08-29 — the detector keeps one filename per variable name
and `path` is rebound in several functions of the same module, so all but the last resolve to
the wrong file. Mapping each name to a SET should have been strictly more permissive. It made
the count WORSE, eight to eleven, and newly flagged `CRISPRGeneEffect.csv`, which is beyond
doubt read. That means the detector's behaviour is not explained by the diagnosis, and the
finding says so:

    Write a test that asserts the detector finds the reader of a known-read file, then fix
    against the test rather than against the count.

This is that test. **Two of its cases are expected to fail today** and are marked xfail with
the reason, so the suite stays green while the defect stays visible — the alternative, a
skipped test, hides it, and a failing suite trains people to ignore red.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

status = pytest.importorskip("status", reason="tools/status.py must be importable")


def sites(rel: str) -> set[str]:
    path = ROOT / rel
    if not path.exists():
        pytest.skip(f"{rel} not present")
    return status._read_sites(path.read_text(encoding="utf-8", errors="replace"))


def test_detector_finds_a_literal_read():
    """The simplest shape: a constant opened directly. If this breaks, nothing else matters."""
    src = 'import pathlib\np = pathlib.Path("a.csv")\np.read_text()\n'
    assert "a.csv" in status._read_sites(src)


def test_detector_finds_a_registry_read():
    """`BY_KEY["hpo_genes"].dest.open()` — the shape most of this repository actually uses."""
    src = (
        'from sieve.pipeline.sources import BY_KEY\n'
        'with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:\n'
        '    fh.read()\n'
    )
    assert "genes_to_disease.txt" in status._read_sites(src)


def test_detector_distinguishes_a_mention_from_a_use():
    """A path that is merely NAMED must not count as read. This is the whole point of the
    AST walk, and it is the property a permissive fix would destroy."""
    src = 'import pathlib\nCN = pathlib.Path("OmicsCNGene.csv")\n'
    assert "OmicsCNGene.csv" not in status._read_sites(src)


@pytest.mark.xfail(
    reason="A37: a local name rebound across functions resolves to only one file, so the "
           "reader of gnomAD constraint in tools/gene_world.py is invisible to the detector. "
           "The obvious fix made the overall count worse and was reverted; see docs/audit.md.",
    strict=False,
)
def test_detector_finds_gnomad_in_gene_world():
    """`tools/gene_world.py` reads gnomAD constraint at line ~127: `path = DATA / "...tsv"`
    followed by `path.open(...)`. `docs/status.md` reports the file as never opened."""
    assert "gnomad.v4.1.constraint_metrics.tsv" in sites("tools/gene_world.py")


@pytest.mark.xfail(
    reason="A37, same cause: the HPA single-cell zip is read in the same module under a "
           "rebound local name.",
    strict=False,
)
def test_detector_finds_hpa_zip_in_gene_world():
    assert "rna_single_cell_type.tsv.zip" in sites("tools/gene_world.py")


def test_the_defect_is_recorded_where_a_reader_would_look():
    """A known-wrong generated document must say so somewhere a reader will find it.

    Without this, the two xfails above are the only trace, and an xfail is invisible in a
    passing run — which is exactly how a defect becomes permanent.
    """
    audit = (ROOT / "docs" / "audit.md").read_text(encoding="utf-8", errors="replace")
    assert "A37" in audit, "the read-site defect must stay recorded in docs/audit.md"
