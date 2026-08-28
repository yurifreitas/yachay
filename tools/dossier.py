#!/usr/bin/env python
"""A per-disease dossier, assembled from real sources and nothing else.

WHAT A DOSSIER HOLDS, and where each part comes from:

    identity      HPO annotation file          names and cross-references
    genetics      HPO gene-to-disease          causal genes
    inheritance   HPO annotations, aspect I    mode, from curated terms
    phenotype     HPO annotations, aspect P    signs WITH FREQUENCY and onset
    epidemiology  Orphanet product9_prev       prevalence band
    onset         Orphanet product9_ages       age of onset and type
    cell axis     Human Protein Atlas          which cell types the genes reach
    current state ClinicalTrials.gov API v2    live trials, phases, interventions

THE FREQUENCY COLUMN IS THE POINT. HPO records how often each sign occurs — as a fraction
like 7/12, or an HPO frequency class. That turns a symptom list into a *distribution*, and
it is the field's own admission of how small the denominators are. A sign recorded as 7/12
carries a 95% interval from roughly 35% to 83%, which is the arithmetic the evidence tab
already makes interactive.

WHAT IS NOT HERE. No severity score, no burden index, no composite. Those require value
judgements this file has no basis for, and inventing one would be the fabrication the
whole atlas argues against. Human impact is reported as onset age, sign frequency and
trial activity — the observable parts — and the reader does the weighing.

    python tools/dossier.py            # build for the default disease set
    python tools/dossier.py --refresh  # re-query ClinicalTrials.gov
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
import html
import re
from xml.etree import ElementTree as ET
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY, ONTOLOGY  # noqa: E402
import sieve as sv  # noqa: E402

RARE = ROOT / "out" / "rare"
TRIAL_CACHE = ONTOLOGY / "trials"
UA = {"User-Agent": "sieve-pipeline/0.1 (research; contact via repository)"}

# The diseases the atlas already discusses. Identified by the EXACT name the catalogue
# uses, never by a hand-written identifier.
#
# The first version of this file hardcoded ORPHA codes from memory and FIVE OF TWELVE WERE
# WRONG: ORPHA:536 returned Adult Refsum disease, ORPHA:79430 returned Hermansky-Pudlak,
# ORPHA:3095 returned atypical rather than classic Rett. Nothing failed — the dossiers
# built cleanly around the wrong diseases, which is the failure mode this whole atlas
# argues about. Resolving the code from the name at build time makes a mismatch loud.
# (catalogue name, the name a trial registry is likely to use)
#
# The two differ, and the gap is measurable: querying ClinicalTrials.gov with the
# catalogue's formal name for NF2 returns ZERO studies, while the name it was called
# before the 2022 rename returns dozens. That is the "two literatures" claim from the
# nomenclature tab, appearing as a live number rather than an argument — so both queries
# are run and both counts are reported.
DISEASE_NAMES = [
    ("Duchenne muscular dystrophy", "Duchenne muscular dystrophy"),
    ("Cystic fibrosis", "Cystic fibrosis"),
    ("Proximal spinal muscular atrophy", "Spinal muscular atrophy"),
    ("Full NF2-related schwannomatosis", "Neurofibromatosis type 2"),
    ("Dravet syndrome", "Dravet syndrome"),
    ("CDKL5-deficiency disorder", "CDKL5 deficiency disorder"),
    ("Zellweger syndrome", "Zellweger syndrome"),
    ("Fibrodysplasia ossificans progressiva", "Fibrodysplasia ossificans progressiva"),
    ("Alkaptonuria", "Alkaptonuria"),
    ("Systemic lupus erythematosus", "Systemic lupus erythematosus"),
    ("Rett syndrome", "Rett syndrome"),
    ("Sickle cell anemia", "Sickle cell disease"),
]


def resolve_diseases() -> list[tuple[str, str, str, str]]:
    """(ORPHA id, OMIM id or '', catalogue name, registry alias).

    Both identifiers are kept because they carry DIFFERENT annotation styles: Orphanet
    entries record frequency as an HPO class ('Frequent'), OMIM entries record it as a
    fraction with a denominator ('7/12'). The denominator is the sample size, so the OMIM
    row is the one that can be given an interval.
    """
    by_name: dict[str, dict[str, str]] = {}
    cols = None
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            if line.startswith("database_id"):
                cols = line.rstrip(chr(10)).split(chr(9))
                continue
            if cols is None:
                continue
            row = dict(zip(cols, line.rstrip(chr(10)).split(chr(9))))
            name = row["disease_name"]
            if name not in by_name:
                by_name[name] = {}
            prefix = row["database_id"].split(":")[0]
            by_name[name].setdefault(prefix, row["database_id"])

    out = []
    for want, alias in DISEASE_NAMES:
        hit = by_name.get(want)
        if not hit:
            print(f"  !! no catalogue entry named exactly {want!r} — skipped")
            continue
        out.append((hit.get("ORPHA", ""), hit.get("OMIM", ""), want, alias))
    return out

# HPO frequency classes, so a class can be shown as an interval rather than a word.
FREQ_CLASS = {
    "HP:0040280": ("Obligate", 1.0, 1.0),
    "HP:0040281": ("Very frequent", 0.80, 0.99),
    "HP:0040282": ("Frequent", 0.30, 0.79),
    "HP:0040283": ("Occasional", 0.05, 0.29),
    "HP:0040284": ("Very rare", 0.01, 0.04),
    "HP:0040285": ("Excluded", 0.0, 0.0),
}
INHERITANCE = {
    "HP:0000006": "Autosomal dominant", "HP:0000007": "Autosomal recessive",
    "HP:0001417": "X-linked", "HP:0001419": "X-linked recessive",
    "HP:0001423": "X-linked dominant", "HP:0001427": "Mitochondrial",
    "HP:0001442": "Somatic mosaicism", "HP:0003745": "Sporadic",
    "HP:0003829": "Incomplete penetrance", "HP:0001450": "Y-linked",
}


def hpo_names() -> dict[str, str]:
    """Term id -> label, from hp.obo. A dossier full of HP:0001250 helps nobody."""
    names: dict[str, str] = {}
    tid = None
    for line in BY_KEY["hpo_terms"].dest.read_text(encoding="utf-8").splitlines():
        if line.startswith("id: HP:"):
            tid = line[4:].strip()
        elif line.startswith("name:") and tid:
            names[tid] = line[5:].strip()
            tid = None
    return names


# The root of the phenotype subontology. Its direct children are the organ-system
# categories every sign ultimately rolls up to.
HPO_PHENOTYPE_ROOT = "HP:0000118"


def hpo_graph() -> tuple[dict[str, set[str]], dict[str, str]]:
    """`is_a` edges and labels from hp.obo.

    WHY THE ONTOLOGY IS READ AS A GRAPH AND NOT A DICTIONARY OF NAMES. Until now this file
    used hp.obo for one thing: turning HP:0001250 into "Seizure". That throws away the part
    that makes HPO an ontology rather than a controlled vocabulary - the `is_a` edges. A
    disease with 39 signs is not a list of 39 facts; it is a distribution over organ
    systems, and the systems are computable from the edges. A flat list cannot answer "what
    does this disease actually attack", which is the first question a clinician asks.

    HPO is a DAG, not a tree: a term legitimately has several parents and rolls up to more
    than one system. That is kept rather than collapsed to a primary system, because
    choosing one would be an authored judgement in a file that has none.
    """
    parents: dict[str, set[str]] = {}
    names: dict[str, str] = {}
    tid = None
    for line in BY_KEY["hpo_terms"].dest.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if line == "[Term]":
            tid = None
        elif line.startswith("id: HP:"):
            tid = line[4:].strip()
            parents.setdefault(tid, set())
        elif line.startswith("name:") and tid:
            names[tid] = line[5:].strip()
        elif line.startswith("is_a: ") and tid:
            parents[tid].add(line[6:].split("!")[0].strip())
    return parents, names


def organ_systems(parents: dict[str, set[str]]) -> dict[str, str]:
    """The top-level categories: the direct children of the phenotype root."""
    return {t: t for t, ps in parents.items() if HPO_PHENOTYPE_ROOT in ps}


def systems_of(term: str, parents: dict[str, set[str]], systems: dict[str, str]) -> set[str]:
    """Every organ system a term rolls up to. Breadth-first over `is_a`, cycle-safe."""
    found: set[str] = set()
    seen = {term}
    queue = [term]
    while queue:
        node = queue.pop()
        if node in systems:
            found.add(node)
        for parent in parents.get(node, ()):
            if parent not in seen:
                seen.add(parent)
                queue.append(parent)
    return found


# ---------------------------------------------------------------------------------------
# WHAT A TRIAL OF THAT SIZE CAN ACTUALLY DETECT — now Stage 2 of the library.
#
# This arithmetic was written here first, inline, because the library had no Stage 2. That
# is how `docs/audit.md` A15 got its example: 10,506 lines of tooling beside a library none
# of it used, with eight of the ten headline stages unimplemented and this one existing as
# a private helper in a script.
#
# It now lives in `sieve.stages.power`, and this file calls it. The numbers are unchanged -
# `tests/test_power.py::test_the_extraction_reproduces_what_it_replaced` pins the published
# portfolio floors so a refactor cannot move a figure that is already in the documentation.
# ---------------------------------------------------------------------------------------
COHEN_LARGE = 0.8


def minimum_detectable_effect(total_n: int) -> float | None:
    """Thin wrapper kept for readability at the call sites. Stage 2 does the work."""
    try:
        return sv.min_detectable_effect(total_n).at()
    except sv.PowerError:
        return None


def parse_frequency(raw: str) -> dict | None:
    """HPO frequency is a fraction, a percentage or a class. Normalise all three, and
    keep the denominator when there is one — it is the sample size."""
    if not raw:
        return None
    if raw in FREQ_CLASS:
        label, lo, hi = FREQ_CLASS[raw]
        return {"kind": "class", "label": label, "lo": lo, "hi": hi, "n": None, "k": None}
    m = re.fullmatch(r"(\d+)/(\d+)", raw)
    if m:
        k, n = int(m.group(1)), int(m.group(2))
        return {"kind": "fraction", "label": raw, "lo": None, "hi": None, "k": k, "n": n,
                "point": round(k / n, 4) if n else None}
    m = re.fullmatch(r"(\d+(?:\.\d+)?)%", raw)
    if m:
        v = float(m.group(1)) / 100
        return {"kind": "percent", "label": raw, "lo": v, "hi": v, "n": None, "k": None}
    return {"kind": "other", "label": raw, "lo": None, "hi": None, "n": None, "k": None}


# THE FOUR EVIDENCE GRADES A SIGN CAN CARRY, and the reason this is a field rather than a
# rendering decision. HPO records a sign frequency as a fraction, a percentage, a class, or
# not at all, and those are NOT four formats of one quantity - they are four different
# amounts of knowledge. "7/12" is an estimate with a sample size. "1/1" is a case report
# wearing the costume of a proportion: its point estimate is 100% and its 95% interval runs
# 21-100%, which is to say it excludes almost nothing. "Very frequent" has no denominator at
# all and cannot be given one. And most signs have nothing.
#
# Collapsing those into one bar chart is how this dashboard came to draw fourteen identical
# bars for Duchenne and read as though it knew something. The grade travels with the sign so
# that no renderer downstream can lose it.
EVIDENCE_GRADES = {
    "quantified": "a fraction with a real denominator - an estimate with a sample size",
    "single-case": "a fraction of one patient - a case report, not a rate",
    "class": "an unquantified frequency class - an interval with no denominator",
    "none": "no frequency recorded at all",
}


def _median(values: list[int]) -> int | None:
    """Median denominator of the quantified signs - the honest headline for "how big were
    the studies behind this symptom list"."""
    vs = sorted(v for v in values if v)
    if not vs:
        return None
    mid = len(vs) // 2
    return vs[mid] if len(vs) % 2 else (vs[mid - 1] + vs[mid]) // 2


def grade_sign(f: dict | None) -> str:
    """Which of the four grades this sign frequency is. The n=1 split is the whole point."""
    if not f or not f.get("kind"):
        return "none"
    if f["kind"] == "fraction":
        return "single-case" if (f.get("n") or 0) <= 1 else "quantified"
    if f["kind"] in ("class", "percent", "other"):
        return "class"
    return "none"


def load_annotations(wanted: set[str]) -> dict:
    """Phenotype, inheritance and onset rows for the diseases we care about."""
    out = defaultdict(lambda: {"phenotype": [], "inheritance": set(), "name": None,
                               "onsetTerms": set()})
    cols = None
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            if line.startswith("database_id"):
                cols = line.rstrip("\n").split("\t")
                continue
            if cols is None:
                continue
            row = dict(zip(cols, line.rstrip("\n").split("\t")))
            did = row["database_id"]
            if did not in wanted:
                continue
            rec = out[did]
            rec["name"] = rec["name"] or row.get("disease_name")
            aspect = row.get("aspect")
            if aspect == "I":
                rec["inheritance"].add(row["hpo_id"])
            elif aspect == "P":
                rec["phenotype"].append({
                    "id": row["hpo_id"],
                    "frequency": parse_frequency(row.get("frequency", "")),
                    "onset": row.get("onset") or None,
                    "sex": row.get("sex") or None,
                    "reference": row.get("reference") or None,
                })
                if row.get("onset"):
                    rec["onsetTerms"].add(row["onset"])
    return out


def load_prevalence_and_ages() -> tuple[dict, dict]:
    """Read the prevalence records with a PARSER, not a regular expression.

    WHY THIS IS NOT A REGEX ANY MORE. It was, and the regex had two independent defects that
    both shipped for months (docs/audit.md A11):

      1. It never decoded `&lt;`, so the `<1 / 1 000 000` class - 4,998 records, the largest
         in the corpus - matched no rank table and was invisible to every output.
      2. `<PrevalenceClass/>` is frequently EMPTY and self-closing. With `re.S` the pattern
         then ran past it and captured the NEXT `<Name>` in the document, which belongs to
         `PrevalenceGeographic`. That fabricated 3,624 prevalence classes that do not exist,
         including the string "Worldwide" 3,616 times.

    The second defect is the one that makes a regex indefensible here: a class and its
    geography must be read from the SAME `<Prevalence>` element or the pairing is fiction,
    and only a parser can guarantee that. tests/test_prevalence_readers_agree.py asserts the
    two readings agree and fails on either defect.
    """
    order = ["<1 / 1 000 000", "1-9 / 1 000 000", "1-9 / 100 000", "1-5 / 10 000",
             "6-9 / 10 000", ">1 / 1000"]
    rank = {p: i for i, p in enumerate(order)}
    prev: dict[str, dict] = {}

    def _text(node, path):
        el = node.find(path)
        return el.text.strip() if el is not None and el.text else None

    for _, disorder in ET.iterparse(str(BY_KEY["orpha_prevalence"].dest), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        code = _text(disorder, "OrphaCode")
        if code:
            # A class and its geography come off the SAME record. This is the pairing the
            # regex could not make, and the reason the spread below can be trusted.
            by_class: dict[str, list[str]] = {}
            classes: list[str] = []
            geos: list[str] = []
            for rec in disorder.findall("./PrevalenceList/Prevalence"):
                cls = _text(rec, "PrevalenceClass/Name")
                geo = _text(rec, "PrevalenceGeographic/Name")
                if geo:
                    geos.append(geo)
                if not cls:
                    continue
                classes.append(cls)
                by_class.setdefault(cls, [])
                if geo and geo not in by_class[cls]:
                    by_class[cls].append(geo)

            ranked = sorted(by_class.items(), key=lambda kv: rank.get(kv[0], 99))
            best = min(classes, key=lambda c: rank.get(c, 99), default=None)
            known = [rank[c] for c in by_class if c in rank]
            prev[f"ORPHA:{code}"] = {
                "rarestBand": best,
                "records": len(classes),
                # `ordered` says whether the band sits on the rarity scale at all.
                # "Unknown" is a real value here and has no position; a renderer that gives
                # it one draws it as the commonest band.
                "spread": [{"band": c, "places": pl, "ordered": c in rank,
                            "rank": rank.get(c)} for c, pl in ranked],
                "distinctBands": len(by_class),
                "spanBands": (max(known) - min(known) + 1) if known else None,
                "geographies": sorted(set(geos))[:6],
            }
        disorder.clear()

    ages: dict[str, list[str]] = {}
    p_ages = BY_KEY.get("orpha_ages")
    if p_ages and p_ages.dest.exists():
        for _, disorder in ET.iterparse(str(p_ages.dest), events=("end",)):
            if disorder.tag != "Disorder":
                continue
            code = _text(disorder, "OrphaCode")
            if code:
                found = {el.text.strip()
                         for el in disorder.iterfind("./AverageAgeOfOnsetList/AverageAgeOfOnset/Name")
                         if el.text}
                if found:
                    ages[f"ORPHA:{code}"] = sorted(found)
            disorder.clear()
    return prev, ages


def load_cells(genes: set[str]) -> dict[str, dict]:
    """For the dossier genes only: top cell type and how many types express it."""
    out: dict[str, dict] = {}
    best: dict[str, tuple[str, float]] = {}
    breadth = Counter()
    with zipfile.ZipFile(BY_KEY["hpa_single_cell"].dest) as z:
        inner = next(n for n in z.namelist() if n.endswith(".tsv"))
        with z.open(inner) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="\t"):
                g = (row.get("Gene name") or "").strip()
                if g not in genes:
                    continue
                try:
                    v = float(row.get("nCPM") or row.get("nTPM") or 0)
                except ValueError:
                    continue
                cell = (row.get("Cell type") or "").strip()
                if v >= 1.0:
                    breadth[g] += 1
                if g not in best or v > best[g][1]:
                    best[g] = (cell, v)
    for g in genes:
        if g in best:
            out[g] = {"topCell": best[g][0], "topValue": round(best[g][1], 1),
                      "expressedIn": breadth.get(g, 0)}
    return out


def fetch_trials(name: str, refresh: bool) -> dict:
    """ClinicalTrials.gov v2. Cached to disk: an artefact that changes under you is not
    reproducible, and re-querying on every build is rude to a public API."""
    TRIAL_CACHE.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    cache = TRIAL_CACHE / f"{slug}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding="utf-8"))
    q = urllib.parse.urlencode({
        "query.cond": name, "pageSize": "200", "format": "json",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,InterventionType,"
                  "InterventionName,StartDate,EnrollmentCount,StudyType",
    })
    url = f"https://clinicaltrials.gov/api/v2/studies?{q}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            data = json.load(r)
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}", "studies": []}
    cache.write_text(json.dumps(data), encoding="utf-8")
    time.sleep(0.4)                      # be a good citizen of a free API
    return data


# WHAT IS ACTUALLY BEING TRIED, as opposed to what kind of thing it is. ClinicalTrials.gov
# types an intervention as DRUG or BIOLOGICAL, which puts an antisense oligonucleotide, a
# steroid and a gene transfer in the same bucket - and those are the three most different
# propositions in rare disease. The classifier below reads the intervention NAME for the
# marks of a modality.
#
# THIS IS THE ONE AUTHORED THING IN THIS FILE, and it is a keyword match, so it is stated as
# such: it will miss a molecule whose name does not carry its class, and it can only find
# what someone wrote in a title. Anything it cannot place is "unclassified" rather than
# guessed, and that count is published beside the others.
MODALITY_MARKS = [
    ("gene therapy", ("aav", "adeno-associated", "gene transfer", "microdystrophin",
                      "delandistrogene", "onasemnogene", "lentivir", "gene therapy")),
    ("oligonucleotide", ("oligonucleotide", "antisense", "eteplirsen", "golodirsen",
                         "casimersen", "viltolarsen", "nusinersen", "sirna", "aso ",
                         "morpholino", "exon skipping", "exon-skipping")),
    ("cell therapy", ("cell therapy", "stem cell", "car-t", "mesenchymal", "transplant")),
    ("gene editing", ("crispr", "base edit", "prime edit", "zinc finger", "talen")),
    ("enzyme replacement", ("enzyme replacement", "alglucosidase", "idursulfase",
                            "laronidase", "agalsidase")),
    ("readthrough", ("ataluren", "readthrough", "read-through")),
    ("corticosteroid", ("prednis", "deflazacort", "corticosteroid", "vamorolone")),
    ("small molecule", ("tablet", "capsule", "oral", "inhibitor", "agonist", "antagonist")),
]


def classify_modality(intervention: dict) -> str:
    """Best-effort modality from the intervention name. Unplaceable is a value, not a gap."""
    name = (intervention.get("name") or "").lower()
    for label, marks in MODALITY_MARKS:
        if any(m in name for m in marks):
            return label
    # No keyword matched. Fall back to the registry's own type rather than to one bucket:
    # "drug, class not stated" and "device" are different amounts of ignorance, and
    # collapsing them would hide which. A brand name with no generic in the title is the
    # commonest reason a drug lands here, and that is a property of the registry entry, not
    # of the therapy.
    kind = (intervention.get("type") or "").upper()
    if kind == "DRUG":
        return "drug, class not stated"
    if kind == "BIOLOGICAL":
        return "biological, class not stated"
    if kind:
        return kind.lower().replace("_", " ")
    return "unclassified"


def summarise_trials(raw: dict) -> dict:
    studies = raw.get("studies", [])
    status, phases, kinds = Counter(), Counter(), Counter()
    interventions = Counter()
    modality = Counter()
    recruiting = []
    enrolment_values: list[int] = []
    interventional_enrolments: list[int] = []
    start_years: list[int] = []
    for s in studies:
        p = s.get("protocolSection", {})
        st = p.get("statusModule", {}).get("overallStatus")
        status[st] += 1
        for ph in p.get("designModule", {}).get("phases", []) or ["NA"]:
            phases[ph] += 1
        kinds[p.get("designModule", {}).get("studyType", "?")] += 1
        for iv in p.get("armsInterventionsModule", {}).get("interventions", []) or []:
            interventions[iv.get("type", "?")] += 1
            modality[classify_modality(iv)] += 1

        n = p.get("designModule", {}).get("enrollmentInfo", {}).get("count")
        if isinstance(n, int):
            enrolment_values.append(n)
            if p.get("designModule", {}).get("studyType") == "INTERVENTIONAL":
                interventional_enrolments.append(n)
        date = (p.get("statusModule", {}).get("startDateStruct", {}) or {}).get("date")
        if isinstance(date, str) and len(date) >= 4 and date[:4].isdigit():
            start_years.append(int(date[:4]))
        if st in ("RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"):
            recruiting.append({
                "nctId": p.get("identificationModule", {}).get("nctId"),
                "title": (p.get("identificationModule", {}).get("briefTitle") or "")[:130],
                "phase": ", ".join(p.get("designModule", {}).get("phases", []) or ["n/a"]),
                "enrollment": p.get("designModule", {}).get("enrollmentInfo", {}).get("count"),
            })
    # ---- the power layer, and the trajectory -------------------------------------------
    # Counted trials answer "is anyone trying". These answer "could it have found anything",
    # which is Stage 2 asked of the clinical record instead of of a screen.
    enrolments = sorted(n for n in enrolment_values if n and n > 0)
    interventional = sorted(n for n in interventional_enrolments if n and n > 0)

    def _median(v):
        return None if not v else (v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) // 2)

    med_all = _median(enrolments)
    med_int = _median(interventional)
    power = {
        "trialsWithEnrolment": len(enrolments),
        "trialsWithoutEnrolment": len(studies) - len(enrolments),
        "medianEnrolment": med_all,
        "medianInterventionalEnrolment": med_int,
        "largest": enrolments[-1] if enrolments else None,
        "smallest": enrolments[0] if enrolments else None,
        # The floor on what the median interventional trial could detect, in standard
        # deviations of its own outcome.
        "medianMDE": minimum_detectable_effect(med_int) if med_int else None,
        # Cohen's conventional large effect is 0.8 SD. A trial that cannot reach it is one
        # that could miss a treatment which genuinely works well.
        # THE PER-ENTITY FORM, from the library. A screen - or a disease's trial record -
        # does not have one sample size; it has one per entity, which is the premise the
        # whole library rests on and the reason Stage 2 exposes this rather than only the
        # scalar above.
        "belowLargeEffect": sv.underpowered(interventional, COHEN_LARGE)["underpowered"],
        "requiredForLargeEffect": sv.required_n(COHEN_LARGE),
        "interventionalWithEnrolment": len(interventional),
        # Read from the stage, not restated. Two copies of an assumptions list is two
        # copies that drift, and this one is load-bearing: it is what stops the floor being
        # quoted as a promise.
        "assumption": sv.min_detectable_effect(100).assumptions,
    }

    # When the first study started, and whether the field is still moving. A count with no
    # time axis cannot distinguish an active programme from a graveyard.
    years = sorted(y for y in start_years if y)
    trajectory = {
        "firstYear": years[0] if years else None,
        "lastYear": years[-1] if years else None,
        "byYear": dict(sorted(Counter(years).items())),
        "startedLastFiveYears": sum(1 for y in years if y >= (years[-1] - 4)) if years else 0,
        "datedTrials": len(years),
    }

    return {
        "total": len(studies),
        "byStatus": dict(status.most_common()),
        "byPhase": dict(phases.most_common()),
        "byType": dict(kinds.most_common()),
        "byIntervention": dict(interventions.most_common()),
        "byModality": dict(modality.most_common()),
        "recruiting": recruiting[:12],
        "recruitingCount": len(recruiting),
        "power": power,
        "trajectory": trajectory,
        "error": raw.get("error"),
    }


def main() -> int:
    RARE.mkdir(parents=True, exist_ok=True)
    refresh = "--refresh" in sys.argv
    labels = hpo_names()

    disease_genes: dict[str, set[str]] = defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g, d = (row.get("gene_symbol") or "").strip(), (row.get("disease_id") or "").strip()
            if g and d:
                disease_genes[d].add(g)

    resolved = resolve_diseases()
    wanted = {i for o, m, _, _a in resolved for i in (o, m) if i}
    ann = load_annotations(wanted)
    prev, ages = load_prevalence_and_ages()
    # The ontology as a graph, not a name table. Built once: 20,413 terms.
    parents, term_names = hpo_graph()
    systems = organ_systems(parents)
    all_genes = {g for o in wanted for g in disease_genes.get(o, set())}
    cells = load_cells(all_genes)

    dossiers = []
    for orpha, omim, query, alias in resolved:
        # Merge the two catalogue entries: Orphanet supplies prevalence and onset, OMIM
        # supplies frequencies with denominators. Neither alone is the whole record.
        rec_o, rec_m = ann.get(orpha, {}), ann.get(omim, {})
        rec = {
            "name": rec_o.get("name") or rec_m.get("name") or query,
            "inheritance": set(rec_o.get("inheritance", set())) | set(rec_m.get("inheritance", set())),
            "phenotype": list(rec_o.get("phenotype", [])) + list(rec_m.get("phenotype", [])),
        }
        genes = sorted(disease_genes.get(orpha, set()) | disease_genes.get(omim, set()))
        phen = rec["phenotype"]

        # Signs, deduplicated, most-supported first. The frequency is kept verbatim so a
        # reader can see the denominator rather than a rounded percentage.
        seen: dict[str, dict] = {}
        for prow in phen:
            key = prow["id"]
            f = prow["frequency"]
            if key not in seen or (f and f.get("n") and not (seen[key]["frequency"] or {}).get("n")):
                seen[key] = prow
        signs = []
        for tid, prow in seen.items():
            f = prow["frequency"] or {}
            signs.append({
                "id": tid,
                "name": labels.get(tid, tid),
                "frequency": f.get("label"),
                "kind": f.get("kind"),
                "evidence": grade_sign(prow["frequency"]),
                "k": f.get("k"), "n": f.get("n"),
                "point": f.get("point") or f.get("lo"),
                "onset": labels.get(prow["onset"], prow["onset"]) if prow["onset"] else None,
                "sex": prow["sex"],
            })
        # ORDER BY HOW MUCH IS KNOWN, THEN BY SAMPLE SIZE. The previous key was
        # (kind != "fraction", -point), which sorted a 1/1 case report - point estimate 1.0 -
        # above a 106/111 series, and so put the weakest evidence in the corpus at the top of
        # the panel. Ranking on the denominator is the argument this whole library makes
        # about screens, applied to a symptom list.
        order = {"quantified": 0, "single-case": 1, "class": 2, "none": 3}
        signs.sort(key=lambda s: (order[s["evidence"]], -(s["n"] or 0), -(s["point"] or 0)))

        # ---- WHAT THIS DISEASE ATTACKS, rolled up the ontology -------------------------
        # A flat list of 39 signs cannot answer "which organ systems does this disease
        # involve", and that is the first question anyone asks. HPO can answer it, because
        # every sign has a path to one or more top-level categories. Crossing the rollup
        # with the evidence grade gives the harder second question: which systems are
        # described but NOT quantified - where the disease is known to act and nobody has
        # measured how often.
        system_rows: dict[str, dict] = {}
        for sign in signs:
            for sys_id in systems_of(sign["id"], parents, systems):
                row = system_rows.setdefault(sys_id, {
                    "id": sys_id,
                    "name": term_names.get(sys_id, sys_id),
                    "signs": 0,
                    "byEvidence": {g: 0 for g in EVIDENCE_GRADES},
                    "examples": [],
                })
                row["signs"] += 1
                row["byEvidence"][sign["evidence"]] += 1
                if len(row["examples"]) < 4:
                    row["examples"].append(sign["name"])
        # A sign can belong to several systems, so these counts sum to more than signCount.
        # Said in the payload rather than left for a reader to discover by adding them up.
        rolled = sorted(system_rows.values(), key=lambda r: -r["signs"])
        unplaced = sum(1 for sign in signs
                       if not systems_of(sign["id"], parents, systems))

        # Both names, so the cost of a rename is a number rather than a claim.
        trials = summarise_trials(fetch_trials(alias, refresh))
        formal = summarise_trials(fetch_trials(query, refresh)) if alias != query else trials
        naming = {
            "catalogueName": query,
            "registryName": alias,
            "catalogueHits": formal["total"],
            "registryHits": trials["total"],
            "lostToTheName": max(0, trials["total"] - formal["total"]),
        }
        gene_cells = {g: cells[g] for g in genes if g in cells}

        dossiers.append({
            "orpha": orpha,
            "omim": omim,
            "query": query,
            "name": rec.get("name") or query,
            "genes": genes,
            "geneCount": len(genes),
            "inheritance": sorted(INHERITANCE.get(t, t) for t in rec.get("inheritance", set())),
            # Named for what it is. There is no key called "prevalence" any more, because
            # a reader of this file should not be able to write one down without noticing
            # that it is a minimum over measurements that disagree.
            "rarestBand": prev.get(orpha, {}).get("rarestBand"),
            "prevalenceSpread": prev.get(orpha, {}).get("spread", []),
            "prevalenceRecords": prev.get(orpha, {}).get("records", 0),
            "prevalenceBands": prev.get(orpha, {}).get("distinctBands", 0),
            "prevalenceSpanBands": prev.get(orpha, {}).get("spanBands"),
            "geographies": prev.get(orpha, {}).get("geographies", []),
            "onsetAges": ages.get(orpha, []),
            # EVERY sign ships, not the first 24. Under the old sort, truncation removed
            # exactly the signs with no frequency at all - so the panel hid the ignorance
            # and rendered the noise, which inverts this project's argument.
            "signs": signs,
            "signCount": len(signs),
            "signsWithDenominator": sum(1 for s in signs if s["n"]),
            "evidence": {
                grade: sum(1 for s in signs if s["evidence"] == grade)
                for grade in EVIDENCE_GRADES
            },
            "evidenceGrades": EVIDENCE_GRADES,
            "medianDenominator": _median([s["n"] for s in signs
                                          if s["evidence"] == "quantified"]),
            "systems": rolled,
            "systemsMeta": {
                "count": len(rolled),
                "unplacedSigns": unplaced,
                "note": (
                    "HPO is a DAG: a sign can roll up to more than one organ system, so "
                    "these counts sum to more than the number of signs. Rolling each sign "
                    "to a single primary system would be an authored judgement, and this "
                    "file makes none."
                ),
                "quantifiedSystems": sum(1 for r in rolled if r["byEvidence"]["quantified"]),
                "describedButUnquantified": sum(
                    1 for r in rolled if not r["byEvidence"]["quantified"]),
            },
            "cells": gene_cells,
            "trials": trials,
            "naming": naming,
        })

    payload = {
        "generated": "2026-08-27",
        "sources": {
            "identity/phenotype/inheritance": "HPO phenotype.hpoa + hp.obo",
            "genes": "HPO genes_to_disease",
            "prevalence/onset": "Orphanet product9_prev / product9_ages (CC BY-ND)",
            "cell axis": "Human Protein Atlas single-cell RNA (CC BY-SA)",
            "current state": "ClinicalTrials.gov API v2, cached locally",
        },
        "caveat": (
            "No severity score, no burden index, no composite. Those need value judgements "
            "this file has no basis for. Human impact is reported as onset age, sign "
            "frequency WITH its denominator, and trial activity — the observable parts. "
            "The reader does the weighing."
        ),
        "dossiers": dossiers,
    }
    (RARE / "dossiers.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("wrote out/rare/dossiers.json")
    print("  %-40s %5s %5s %5s %6s %5s %s"
          % ("disease", "genes", "signs", "w/ n", "trials", "recr.", "lost to the name"))
    for d in dossiers:
        lost = d["naming"]["lostToTheName"]
        print("  %-40s %5d %5d %5d %6d %5d %s"
              % (d["name"][:40], d["geneCount"], d["signCount"], d["signsWithDenominator"],
                 d["trials"]["total"], d["trials"]["recruitingCount"],
                 f"{lost} ({d['naming']['catalogueHits']} -> {d['naming']['registryHits']})"
                 if lost else "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
