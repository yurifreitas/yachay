"""One parser for MONDO, because four of them is four chances to disagree.

WHY THIS EXISTS. `data/ontology/mondo.obo` is 53 MB and four tools each read it whole and
each hand-rolled its own OBO parser over it:

  * `tools/gap_taxonomy.py`      — ids and xrefs, for the OMIM/ORPHA crosswalk
  * `tools/lexicon_check.py`     — ids, names, xrefs and the obsolete flag
  * `tools/single_cell_coverage.py` — ids, names and xrefs, written months later
  * `tools/tropical_gap.py`      — ids, names, synonyms and obsolescence

Four parsers of one grammar is 212 MB of redundant reading, which is the cheap complaint. The
expensive one is that they can DISAGREE: three of the four treat an obsolete term differently,
two split `xref:` on whitespace and one takes the first space-delimited token, and nothing
compares them. Two tools reporting different counts for the same ontology, both looking
correct, is exactly the failure this repository keeps building checks against.

`tools/tropical_gap.py` made it worse by reading `DATA / "mondo.obo"` directly rather than
through `sources.BY_KEY`, so it would silently break the day a source moved — and a source
moved this week, when `Source` gained a `subdir` so the GWAS files could live outside
`data/ontology/`.

WHAT THIS DOES NOT DO. It is not a general OBO library and does not try to be. It reads the
four fields those tools actually use, in one pass, and caches the result for the life of the
process. A tool needing a field it does not carry should add it here rather than open the file
again.
"""
from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field

from .sources import BY_KEY

#: Synonym payloads are quoted in OBO: `synonym: "alpha thalassemia" EXACT []`.
_QUOTED = re.compile(r'"([^"]+)"')


@dataclass
class MondoTerm:
    """One term, with the fields this repository actually reads."""

    id: str
    name: str | None = None
    obsolete: bool = False
    xrefs: set[str] = field(default_factory=set)
    synonyms: list[str] = field(default_factory=list)

    def ids_in(self, prefix: str) -> set[str]:
        """Cross-references in one namespace, normalised.

        Orphanet appears as `Orphanet:1234` and this repository writes `ORPHA:1234`
        everywhere else. Doing that conversion here, once, is the reason a shared parser is
        worth more than a shared file read: the previous four copies each did it inline and
        two of them spelled it differently.
        """
        want = prefix.lower()
        out = set()
        for x in self.xrefs:
            head, _, tail = x.partition(":")
            if head.lower() == want and tail:
                out.add(f"{'ORPHA' if want == 'orphanet' else head.upper()}:{tail}")
        return out


@functools.lru_cache(maxsize=1)
def load_mondo() -> dict[str, MondoTerm]:
    """Every MONDO term by id, parsed once per process.

    Cached because four callers in one pipeline run would otherwise read 53 MB four times.
    The cache is keyed on nothing — there is one MONDO file — so a caller that needs a
    re-read after the file changes should call `load_mondo.cache_clear()` and say why.
    """
    path = BY_KEY["mondo"].dest
    if not path.exists():
        return {}

    terms: dict[str, MondoTerm] = {}
    cur: MondoTerm | None = None
    in_term = False

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.rstrip()
        if line.startswith("["):
            # Any stanza header ends the previous term. Only [Term] opens a new one, so
            # [Typedef] blocks — which also carry `id:` and `name:` — cannot leak in. Two of
            # the four previous parsers had that hole.
            in_term = line == "[Term]"
            cur = None
        elif not in_term:
            continue
        elif line.startswith("id: "):
            tid = line[4:].strip()
            cur = MondoTerm(id=tid)
            terms[tid] = cur
        elif cur is None:
            continue
        elif line.startswith("name: "):
            cur.name = line[6:].strip()
        elif line.startswith("xref: "):
            cur.xrefs.add(line[6:].split()[0].strip())
        elif line.startswith("synonym: "):
            m = _QUOTED.search(line)
            if m:
                cur.synonyms.append(m.group(1))
        elif line.startswith("is_obsolete: true"):
            cur.obsolete = True

    return terms


def live_terms() -> dict[str, MondoTerm]:
    """Terms that are not marked obsolete.

    Separated from `load_mondo` rather than filtered inside it because two of the four
    previous parsers wanted obsolete terms and two did not — and a shared loader that silently
    drops rows is worse than four parsers, not better.
    """
    return {k: t for k, t in load_mondo().items() if not t.obsolete}


def crosswalk() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """OMIM -> ORPHA and ORPHA -> OMIM, through MONDO's cross-references.

    This is the join `tools/gap_taxonomy.py` uses to type a missing field as an
    interoperability gap — a fact that exists in one catalogue and not the other. It is
    the single most reused derivation in this repository and it now has one implementation.
    """
    omim_to_orpha: dict[str, set[str]] = {}
    orpha_to_omim: dict[str, set[str]] = {}
    for term in load_mondo().values():
        omims = term.ids_in("OMIM")
        orphas = term.ids_in("Orphanet")
        if not omims or not orphas:
            continue
        for o in omims:
            omim_to_orpha.setdefault(o, set()).update(orphas)
        for o in orphas:
            orpha_to_omim.setdefault(o, set()).update(omims)
    return omim_to_orpha, orpha_to_omim
