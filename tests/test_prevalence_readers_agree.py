"""Two tools reading one file must agree about what is in it.

WHY THIS TEST EXISTS. On 2026-08-27 the repository was found to be reading the Orphanet
prevalence XML two different ways and getting two different answers, for months:

  * `tools/prevalence_audit.py` and `tools/ancestry_geography.py` use `ElementTree`, which
    decodes XML entities. They saw 4,998 records in the `<1 / 1 000 000` class.
  * `tools/build_atlas.py`, `tools/dossier.py` and `tools/atlas_bias.py` used a regular
    expression over the raw text, which does not. They saw that class as the literal string
    `&lt;1 / 1 000 000`, it matched no entry in their rank tables, and **3,987 diseases -
    the largest band in the catalogue - were invisible to every one of their outputs.**

The rendered dashboard read "380 of 770 ultra-rare, and no gene". The true figure was 4,586
ultra-rare, 1,923 without a gene. A membership test naming the missing class was dead code
that could never fire. Full account: docs/audit.md A11.

A second defect surfaced while writing this file, and it is why the invariant below is
worded the way it is. `<PrevalenceClass/>` is frequently EMPTY and self-closing; with
`re.S` the pattern then ran past it and captured the next `<Name>` in the document, which
belongs to `PrevalenceGeographic`. That fabricated **3,624 prevalence classes that do not
exist**, "Worldwide" 3,616 times among them - and it silently corrupted any pairing of a
class with the country that reported it.

WHAT IS ASSERTED. Not that a particular number is right - that would need updating whenever
Orphanet publishes. And not that the regex and the parser agree: they cannot be made to,
because the second defect is intrinsic to the pattern rather than a missing call. The
invariant is therefore structural and permanent: **no tool reads a prevalence class with a
regular expression.** Everything reads this file with `ElementTree`, and the test fails the
moment something goes back.

The test skips when the corpus is absent, because a missing download is not a defect.
"""

from __future__ import annotations

import html
import pathlib
import re
from collections import Counter
from xml.etree import ElementTree as ET

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
XML = ROOT / "data" / "ontology" / "en_product9_prev.xml"

# The pattern the tools use, kept here verbatim. If a tool changes its pattern this test is
# the place that notices the two have drifted apart.
CLASS_RE = re.compile(
    r"<PrevalenceClass[^>]*>.*?<Name lang=\"en\">([^<]+)</Name>", re.S
)


def _by_parser() -> Counter:
    """What the corpus contains, according to a real XML parser."""
    counts: Counter = Counter()
    for _, disorder in ET.iterparse(str(XML), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        for prev in disorder.findall("./PrevalenceList/Prevalence"):
            el = prev.find("PrevalenceClass/Name")
            if el is not None and el.text:
                counts[el.text.strip()] += 1
        disorder.clear()
    return counts


def _by_regex(unescape: bool) -> Counter:
    """What the corpus contains according to the regex path, with and without the fix."""
    text = XML.read_text(encoding="utf-8", errors="replace")
    found = CLASS_RE.findall(text)
    return Counter(html.unescape(c) if unescape else c for c in found)


requires_corpus = pytest.mark.skipif(
    not XML.exists(), reason="Orphanet corpus not downloaded; run python tools/ingest.py"
)


def test_no_tool_reads_prevalence_classes_with_a_regex():
    """The invariant the repository now guarantees, and the stronger one.

    The first version of this test asserted that the regex and the parser AGREE once
    entities are decoded. It failed - and it was right to. Decoding `&lt;` fixes only the
    first defect; the second is intrinsic to the pattern, because `<PrevalenceClass/>` is
    frequently empty and self-closing and no amount of unescaping stops `.*?` from running
    past it into the next element. The two readers cannot be made to agree.

    So the guarantee is not "the regex is correct" but "there is no regex". Every tool now
    reads this file with `ElementTree`. This test fails the moment one goes back.
    """
    offenders = []
    for path in sorted((ROOT / "tools").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        # Only flag a live regex, not the several comments that quote the pattern while
        # explaining why it was removed.
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "PrevalenceClass" in stripped and (
                "re.findall" in stripped or "re.search" in stripped or "re.compile" in stripped
            ):
                offenders.append(f"{path.name}: {stripped[:80]}")
    assert not offenders, (
        "prevalence classes must be read with a parser, not a regex:\n  "
        + "\n  ".join(offenders)
    )


@requires_corpus
def test_the_defect_is_reproducible_without_the_fix():
    """The regression case, kept so the bug cannot be re-introduced as a 'simplification'.

    Without `html.unescape` the two readers disagree, and they disagree on the class that
    matters most: the rarest one. Asserting the FAILURE keeps the reason for the fix
    executable rather than only described in a comment.
    """
    raw = _by_regex(unescape=False)
    parsed = _by_parser()

    assert raw != parsed, "entities decoded upstream — this test's premise no longer holds"

    rarest = "<1 / 1 000 000"
    assert parsed[rarest] > 0, "the corpus should contain the rarest class"
    assert raw[rarest] == 0, "the un-decoded reader should be blind to it"
    assert raw[html.escape(rarest)] == parsed[rarest], (
        "the records are not lost, they are mis-keyed under the escaped string — which is "
        "exactly why the defect was silent"
    )


@requires_corpus
def test_no_class_string_carries_an_undecoded_entity():
    """A directly readable statement of the failure mode, for anyone reading the outputs."""
    for label in _by_parser():
        assert "&lt;" not in label and "&gt;" not in label and "&amp;" not in label, (
            f"prevalence class {label!r} still carries an XML entity"
        )
