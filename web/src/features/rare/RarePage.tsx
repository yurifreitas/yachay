/** The rare-disease atlas — a page whose subject is what is NOT known.
 *
 *  It exists because the fit assessment in `docs/references/broad-institute-fit.md` kept
 *  running into the same wall: the shape of a rare-disease problem is not "rank these
 *  candidates" but "most of the fields are empty, and the emptiness is patterned". A
 *  dashboard that renders empty fields as blanks under-reports that, so here every gap is
 *  a typed value with its own mark.
 *
 *  Composition only: the page picks the data, holds the two pieces of view state, and
 *  hands slots to organisms. Nothing below an organism knows what a disease is.
 */
import { Suspense, lazy, useMemo, useState } from "react";
import { lexicon } from "./data/lexicon";
import { atlas } from "./data/atlas";
import { nongeneMeasured } from "./data/nongeneMeasured";
import { sortDiseases, type SortKey } from "./model";
import { GapMatrix } from "./components/GapMatrix";
import { OntologyLegend } from "./components/OntologyLegend";
import { DiseaseCard } from "./components/DiseaseCard";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { RARE } from "../../i18n/strings";
import { TROP } from "../../i18n/tropical";
import { useT } from "../../i18n";
import { StatusDot } from "../../components/atoms/StatusDot";
import { Chip } from "../../components/atoms/Chip";
import css from "./RarePage.module.css";

/** Sections are mutually exclusive, so they are the natural code-split boundary: the
 *  network, the charts and the capability tables are not downloaded until the reader
 *  opens the question that needs them. Each is named so the chunk is legible in a build
 *  report rather than appearing as a hash. */
const EvidenceLab = lazy(() => import("./components/EvidenceLab").then((m) => ({ default: m.EvidenceLab })));
const ApproachChooser = lazy(() => import("./components/ApproachChooser").then((m) => ({ default: m.ApproachChooser })));
const CellVsGene = lazy(() => import("./components/CellVsGene").then((m) => ({ default: m.CellVsGene })));
const WorldAtlas = lazy(() => import("./components/WorldAtlas").then((m) => ({ default: m.WorldAtlas })));
const BiasAudit = lazy(() => import("./components/BiasAudit").then((m) => ({ default: m.BiasAudit })));
const Nomenclature = lazy(() => import("./components/Nomenclature").then((m) => ({ default: m.Nomenclature })));
const Dimensions = lazy(() => import("./components/Dimensions").then((m) => ({ default: m.Dimensions })));
const DimensionsTwo = lazy(() => import("./components/DimensionsTwo").then((m) => ({ default: m.DimensionsTwo })));
const Dossier = lazy(() => import("./components/Dossier").then((m) => ({ default: m.Dossier })));
const Capability = lazy(() => import("./components/Capability").then((m) => ({ default: m.Capability })));
const GrowingNetwork = lazy(() => import("./components/GrowingNetwork").then((m) => ({ default: m.GrowingNetwork })));
const SparseStructure = lazy(() => import("./components/SparseStructure").then((m) => ({ default: m.SparseStructure })));
const References = lazy(() => import("./components/References").then((m) => ({ default: m.References })));
const Thesis = lazy(() => import("./components/Thesis").then((m) => ({ default: m.Thesis })));
const NonGene = lazy(() => import("./components/NonGene").then((m) => ({ default: m.NonGene })));
const Ancestry = lazy(() => import("./components/Ancestry").then((m) => ({ default: m.Ancestry })));
const SelfAudit = lazy(() => import("./components/SelfAudit").then((m) => ({ default: m.SelfAudit })));
const GapPatterns = lazy(() => import("./components/GapPatterns").then((m) => ({ default: m.GapPatterns })));
const TropicalGap = lazy(() => import("./components/TropicalGap").then((m) => ({ default: m.TropicalGap })));
const PatientEvidence = lazy(() => import("./components/PatientEvidence").then((m) => ({ default: m.PatientEvidence })));


/** TWO LEVELS, BECAUSE THIRTEEN FLAT TABS STOPPED BEING A MAP.
 *
 *  The nav wrapped onto two lines and turned into a list to be scanned rather than a set of
 *  questions to be chosen between, and nothing announced what was inside a tab before it was
 *  clicked. So the sections are grouped by the QUESTION they answer, the group row states
 *  those questions and how many sections each holds, and the section row underneath is short
 *  enough to read in one pass.
 *
 *  The order inside a group is still a workflow and not a table of contents: look at one
 *  disease, then at what stops it, then at what it would physically take.
 *
 *  Both levels are URL state, so every view in the dashboard is a link someone can send.
 */
const GROUPS: NavGroupDef[] = [
  { id: "known", label: RARE.gKnown, question: RARE.qKnown },
  { id: "cause", label: RARE.gCause, question: RARE.qCause },
  { id: "case", label: RARE.gCase, question: RARE.qCase },
  { id: "decide", label: RARE.gDecide, question: RARE.qDecide },
  { id: "argument", label: RARE.gArgument, question: RARE.qArgument },
];

const SECTIONS: NavSectionDef[] = [
  // 1. The catalogue, and what its numbers are really measuring. First, because a reader who
  //    meets one disease before meeting the denominator has no way to weigh it.
  { id: "world", label: RARE.sWorld, group: "known" },
  { id: "bias", label: RARE.sBias, group: "known" },
  { id: "population", label: RARE.sPopulation, group: "known" },
  { id: "patients", label: RARE.sPatients, group: "known" },
  { id: "names", label: RARE.sNames, group: "known" },
  { id: "atlas", label: RARE.sAtlas, group: "known" },
  { id: "gaps", label: RARE.sGaps, group: "known" },
  { id: "tropical", label: TROP.section, group: "known" },

  // 2. What a disease is OF — the ladder's middle rungs, in order of scale.
  { id: "cell", label: RARE.sCell, group: "cause" },
  { id: "network", label: RARE.sNetwork, group: "cause" },
  { id: "sparse", label: RARE.sSparse, group: "cause" },
  { id: "nongene", label: RARE.sNongene, group: "cause" },

  // 3. One record in full, then the physics and the payroll a therapy would need.
  { id: "disease", label: RARE.sDisease, group: "case" },
  { id: "capability", label: RARE.sCapability, group: "case" },

  // 4. Deciding: what the evidence carries, then choosing under constraint.
  { id: "evidence", label: RARE.sEvidence, group: "decide" },
  { id: "choose", label: RARE.sChoose, group: "decide" },
  { id: "dims", label: RARE.sDims, group: "decide" },

  // 5. The argument and its provenance — a thesis and its bibliography are one thing.
  { id: "thesis", label: RARE.sThesis, group: "argument" },
  { id: "selfaudit", label: RARE.sSelfAudit, group: "argument" },
  { id: "refmap", label: RARE.sRefmap, group: "argument" },
  { id: "sources", label: RARE.sSources, group: "argument" },
];


const SORTS: { id: SortKey; label: string }[] = [
  { id: "gaps", label: "Most unknown first" },
  { id: "rarity", label: "Rarest first" },
  { id: "name", label: "A–Z" },
];

export default function RarePage() {
  const [sort, setSort] = useState<SortKey>("gaps");
  const [selected, setSelected] = useState<string | null>(null);
  // Both nav levels live in the URL and are drawn by the rail, not by this page.
  const tt = useT();
  const { section } = useSectionNav({
    owner: "rare", groups: GROUPS, sections: SECTIONS, initial: "world",
  });

  const ordered = useMemo(
    () => sortDiseases(lexicon, lexicon.diseases, sort),
    [sort]
  );
  const focus = ordered.find((d) => d.name === selected) ?? ordered[0];

  // The lexicon is a build artifact and can legitimately be missing. Say so, and say how
  // to produce it, rather than rendering an atlas of nothing.
  if (!lexicon.diseases.length) {
    return (
      <section className={css.page}>
        <div className={css.empty}>
          <span className={css.emptyTitle}>No lexicon has been generated yet</span>
          <p className={css.sub}>
            The atlas reads a build artifact. Generate it, then rebuild the explorer's data.
          </p>
          <code className={css.emptyHint}>python tools/rare_disease_seed.py</code>
        </div>
      </section>
    );
  }

  return (
    <section className={css.page}>
      <header className={css.hero}>
        <div className={css.heroTop}>
        <div className={css.heroText}>
          <p className={css.eyebrow}>Rare and ultra-rare disease · decision support</p>
          <h2 className={css.title}>Most of what there is to know about a rare disease is a field nobody has filled in</h2>
        </div>
        <div className={css.heroSide}>
          <p className={css.lede}>
            The join across HPO, Orphanet and the Human Protein Atlas reaches{" "}
            <strong>{atlas.scale.diseases.toLocaleString("en-US")}</strong> catalogue entries
            — more than the <strong>7,000–8,000</strong> distinct diseases usually quoted,
            because OMIM, Orphanet and DECIPHER each describe the same conditions at
            different grain. The counters are measured on that join, not asserted: each one
            is a place the data stops.
          </p>
        </div>
        </div>
        {/* MEASURED ON THE ATLAS, NOT ON THE SEED. These counters used to read "3 of 12" —
            the denominators of the twelve-disease demonstration lexicon — under a headline
            that speaks for the whole field. The seed is still on the page and still labelled
            as a demonstration; it just no longer supplies the hero's statistics.
            "No approved therapy" is gone rather than rescaled: none of the ingested sources
            records approved therapies, so there was no honest denominator at any size. */}
        <div className={css.counters}>
          <Counter n={atlas.scale.diseases - atlas.scale.diseasesWithGene}
                   of={atlas.scale.diseases} label="no causal gene found" tone="unknown" />
          <Counter n={atlas.scale.diseases - atlas.scale.diseasesPlaceableOnCellAxis}
                   of={atlas.scale.diseases} label="cannot be placed on the cell axis" tone="unknown" />
          <Counter n={atlas.scale.ultraRare - atlas.scale.ultraRareWithGene}
                   of={atlas.scale.ultraRare} label="ultra-rare, and no gene" tone="absent" />
          <Counter n={nongeneMeasured.geneLessBreakdown.withNoInheritanceAnnotation}
                   of={nongeneMeasured.geneLessBreakdown.total}
                   label="gene-less, and no inheritance recorded either" tone="unknown" />
        </div>
      </header>

      <SectionHeading />

      <Suspense key={section} fallback={<SectionSkeleton />}>

      {section === "tropical" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>{tt(TROP.heading)}</h3>
            <p className={css.sub}>{tt(TROP.sub)}</p>
          </div>
          <TropicalGap />
        </section>
      )}

      {section === "gaps" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>The blanks are not scattered — they land on the same diseases</h3>
            <p className={css.sub}>
              The matrix on &ldquo;Where the data stops&rdquo; shows which fields are empty for
              one disease at a time, and structurally cannot show which are empty
              <em> together</em>. This counts the patterns over every OMIM-coded disease in the
              HPO annotation file. If the gaps were independent, most diseases with a gap would
              have exactly one; they do not.
            </p>
          </div>
          <GapPatterns />
        </section>
      )}

      {section === "disease" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>One disease at a time, assembled from every source and nothing invented</h3>
            <p className={css.sub}>
              Genes, signs with their denominators, prevalence, onset, the cell types the
              genes reach, and what is being tried right now. No severity score — that would
              need a value judgement this project has no basis for.
            </p>
          </div>
          <Dossier />
        </section>
      )}

      {section === "selfaudit" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>
              Twenty layers make overlapping claims. Nothing used to check whether they agree
            </h3>
            <p className={css.sub}>
              Every other section here reports a gap in somebody else&rsquo;s data. This one
              reports the gaps in ours: where two of our own layers contradict each other,
              whether the authored identifiers actually resolve against the catalogues, and
              what the field&rsquo;s evidence looks like when all 267,782 annotations are
              graded rather than twelve diseases. A dashboard that keeps its own
              contradictions in a file nobody opens is publishing them nowhere.
            </p>
          </div>
          <SelfAudit />
        </section>
      )}

      {section === "patients" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>
              Ten thousand individual people, and what they say about the catalogue
            </h3>
            <p className={css.sub}>
              Every other section here reads an aggregate: it can say a disease involves
              seizures and that a gene has nonsense variants. This one reads 10,377 patients,
              and the difference is a denominator. Where the catalogue rests a frequency on
              <strong> one patient</strong> it reads 0.932 and the patients say 0.436 — a
              difference whose 95 % interval is nowhere near zero.
            </p>
          </div>
          <PatientEvidence />
        </section>
      )}

      {section === "population" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>
              A prevalence is a property of a disorder <em>in a population</em>, and this
              catalogue records it as a scalar
            </h3>
            <p className={css.sub}>
              Orphanet stamps every prevalence record with a geography. Eleven analytical
              layers on this dashboard were built on that corpus and none of them had read
              the column. Reading it says that 73.5% of the disorders measured in more than
              one country disagree about which prevalence band they are in — and that the
              world&rsquo;s reference epidemiology is proportional to Europe, not to the
              world.
            </p>
          </div>
          <Ancestry />
        </section>
      )}

      {section === "world" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>Every rare disease the field has catalogued, and where the data stops</h3>
            <p className={css.sub}>
              Joined from HPO, Orphanet and the Human Protein Atlas — not hand-written. The
              size is not the finding; how far the join gets before it runs out is.
            </p>
          </div>
          <WorldAtlas />
        </section>
      )}

      {section === "capability" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>An approach is a room, an instrument, a physical limit and a payroll</h3>
            <p className={css.sub}>
              Every other tab says what is known. This one says what it would take: the
              instrument each stage is gated on, the physics that makes it unsubstitutable,
              the capital as a band rather than a figure, and the whole-time-equivalent staff
              — which is usually the column that is missing when a plan fails.
            </p>
          </div>
          <Capability />
        </section>
      )}

      {section === "nongene" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>Every join on this site is keyed on a gene. This is what the key misses</h3>
            <p className={css.sub}>
              The atlas finds no causal gene for 3,801 of 14,831 diseases, and a disease
              without a gene is not merely missing a column — it is invisible to the cell
              axis, to the dependency screen and to every ranking here. So: when the causal
              unit is not a gene, what is it, and what fills each slot the gene fills?
            </p>
          </div>
          <NonGene />
        </section>
      )}

      {section === "refmap" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>Eighty-four references, and the bridge they were supposed to demonstrate</h3>
            <p className={css.sub}>
              The map spans NF2 clinical work, gene therapy, rare-disease infrastructure,
              network biology, sparse HPC, tensor compilers and complex systems. Tagging each
              entry with its community and the ladder rung it serves turns the map into an
              audit — and the audit does not say what the map was assembled to say.
            </p>
          </div>
          <References />
        </section>
      )}

      {section === "thesis" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>The argument these measurements serve, with its own register kept intact</h3>
            <p className={css.sub}>
              Every other section here is a measurement. This one is the thesis they were taken
              for — a ladder from genotype to patient, eighteen claims each marked as founded
              or hypothetical, and an audit of which of them this repository has actually
              built. Six are named and not built; three are absent. That is said at the same
              weight as the claims.
            </p>
          </div>
          <Thesis />
        </section>
      )}

      {section === "dims" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>Seventeen people who changed how a field sees, each one actually run</h3>
            <p className={css.sub}>
              Each supplies a transform applied to the data already here. A name that yields
              no computation is marked as such rather than invoked — and the second group
              exists because the first one was all men, which was not an accident.
            </p>
          </div>
          <Dimensions />
          <DimensionsTwo />
        </section>
      )}

      {section === "names" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>A name is upstream of every statistic on this page</h3>
            <p className={css.sub}>
              Etymology, the six naming eras still in simultaneous use, and what each name
              costs — including two that preserve a theory the field has abandoned and four
              withdrawn on ethical grounds.
            </p>
          </div>
          <Nomenclature />
        </section>
      )}

      {section === "bias" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>Which numbers measure the world, and which measure who did the measuring</h3>
            <p className={css.sub}>
              A catalogue is a screen. This library's own argument applies to its own
              reference data — including one chart on the previous tab, and one sentence
              this dashboard had already published.
            </p>
          </div>
          <BiasAudit />
        </section>
      )}

      {section === "choose" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>Which approach fits the programme you actually have</h3>
            <p className={css.sub}>
              Set your constraints on the left and your priorities below them. The model
              ranks the modalities and shows the contribution of every criterion, because a
              ranking without its decomposition is an opinion wearing a number.{" "}
              <strong>Not clinical guidance</strong> — a structured way to make assumptions
              explicit and disagree with them.
            </p>
          </div>
          <ApproachChooser />
        </section>
      )}

      {section === "evidence" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>What a case series of four patients can actually support</h3>
            <p className={css.sub}>
              Ultra-rare literature is written in percentages drawn from single-digit series,
              and those percentages go on to shape registries, endpoints and n-of-1
              protocols. Set the two numbers that exist in the paper and read the three the
              paper does not print.
            </p>
          </div>
          <EvidenceLab />
        </section>
      )}

      {section === "cell" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>Naming the gene rarely tells you what to do; naming the cell often does</h3>
            <p className={css.sub}>
              Lupus, as the disease that makes this repository's own premise clinical — and
              as the case that sits on the rare-disease boundary rather than inside or
              outside it.
            </p>
          </div>
          <CellVsGene />
        </section>
      )}

      {section === "network" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>A network that grows, instead of a diagram that does not</h3>
            <p className={css.sub}>
              The real gene-gene graph — 5,524 genes, adjacent when they cause a common
              disease. Pick a seed, click to expand, double-click to add a second seed. The
              colour and the radius are a random walk with restart recomputed over whatever you
              have opened, so the picture is different every time because you built it.
            </p>
          </div>
          <GrowingNetwork />
        </section>
      )}

      {section === "sparse" && (
        <section className={css.block}>
          <div>
            <h3 className={css.h3}>The same graph, as a sparse matrix, against its own null</h3>
            <p className={css.sub}>
              The reference audit found that the biological and computational literatures here
              never talk about the same object. This is that object, measured: modularity,
              degree skew, and whether reordering by biological community improves memory
              locality more than it does on a rewiring with the identical degree sequence.
            </p>
          </div>
          <SparseStructure />
        </section>
      )}

      {section === "atlas" && (
        <>
          <section className={css.block}>
            <div className={css.blockHead}>
              <div>
                <h3 className={css.h3}>The pipeline stops earlier for some diseases than for others</h3>
                <p className={css.sub}>
                  One row per disease, one column per axis. The pipeline reads left to right:
                  you need the gene before the mechanism, and the mechanism before a therapy.
                </p>
              </div>
              <div className={css.controls} role="group" aria-label="Sort the table">
                {SORTS.map((o) => (
                  <button
                    key={o.id}
                    type="button"
                    className={sort === o.id ? css.tabOn : css.tab}
                    aria-pressed={sort === o.id}
                    onClick={() => setSort(o.id)}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>

            <div className={css.legendRow}>
              <StatusDot state="known" label="known" size="sm" />
              <StatusDot state="partial" label="partly known" size="sm" />
              <StatusDot state="unknown" label="nobody knows" size="sm" />
              <StatusDot state="absent" label="does not exist yet" size="sm" />
            </div>

            <GapMatrix lexicon={lexicon} diseases={ordered} />
          </section>

          <section className={css.block}>
            <div className={css.blockHead}>
              <div>
                <h3 className={css.h3}>One entry in full</h3>
                <p className={css.sub}>
                  The identifiers it carries, what is known along each axis, and every name
                  the literature searches it by — including the ones not written in Latin
                  script.
                </p>
              </div>
              <div className={css.controls} role="group" aria-label="Choose a disease">
                {ordered.slice(0, 6).map((d) => (
                  <button
                    key={d.name}
                    type="button"
                    className={focus?.name === d.name ? css.tabOn : css.tab}
                    aria-pressed={focus?.name === d.name}
                    onClick={() => setSelected(d.name)}
                  >
                    {d.name.length > 26 ? d.name.slice(0, 24) + "\u2026" : d.name}
                  </button>
                ))}
              </div>
            </div>
            {focus && <DiseaseCard d={focus} />}
          </section>
        </>
      )}

      {section === "sources" && (
        <>
          <div className={css.warn} role="note">
            <strong>This is a schema demonstration, not a reference database.</strong>{" "}
            {lexicon.provenance}
          </div>

          <section className={css.block}>
            <h3 className={css.h3}>Six systems index the same disease, and none is a superset of the others</h3>
            <p className={css.sub}>
              Each was built for a different job. MONDO exists specifically to merge them,
              which is the clearest statement that the fragmentation is real.
            </p>
            <OntologyLegend ontologies={lexicon.ontologies} />
          </section>

          <section className={css.block}>
            <h3 className={css.h3}>&ldquo;Rare&rdquo; is not one definition</h3>
            <p className={css.sub}>
              The threshold is set by jurisdiction, and two of the four are absolute counts
              rather than rates — so whether a disease is rare depends on where the patient
              lives and how many people live there.
            </p>
            <div className={css.defs}>
              {lexicon.definitions.map((d) => (
                <div key={d.where} className={css.def}>
                  <span className={css.defWhere}>{d.where}</span>
                  <span className={css.defRule}>{d.rule}</span>
                  <Chip tone={d.basis === "prevalence" ? "known" : "partial"}>{d.basis}</Chip>
                  <span className={css.defSrc}>{d.source}</span>
                </div>
              ))}
            </div>
          </section>

          <section className={css.block}>
            <h3 className={css.h3}>Two of the seven headline numbers come from a primary source; five do not</h3>
            <p className={css.sub}>
              Every number quoted at the top of this page appears here with the check that
              would verify it.
            </p>
            <ul className={css.facts}>
              {lexicon.fieldFacts.map((f) => (
                <li key={f.claim} className={css.fact}>
                  <StatusDot
                    state={f.confidence === "high" ? "known" : f.confidence === "medium" ? "partial" : "unknown"}
                    label={f.confidence}
                    size="sm"
                  />
                  <span className={css.factClaim}>{f.claim}</span>
                  <span className={css.factVerify}>{f.verify}</span>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
      </Suspense>
    </section>
  );
}

function Counter({
  n, of, label, tone,
}: { n: number; of: number; label: string; tone: "unknown" | "absent" }) {
  const share = of ? n / of : 0;
  return (
    <article className={css.counter}>
      <span className={css.counterL}>{label}</span>
      <div className={css.counterRow}>
        <span className={css.counterN}>{n.toLocaleString("en-US")}</span>
        <span className={`${css.counterShare} ${tone === "unknown" ? css.shareUnknown : css.shareAbsent}`}>
          {Math.round(share * 100)}% of {of.toLocaleString("en-US")}
        </span>
      </div>
      <span className={css.counterBar}>
        <span
          className={`${css.counterFill} ${tone === "unknown" ? css.fillUnknown : ""}`}
          style={{ width: `${Math.round(share * 100)}%` }}
        />
      </span>
    </article>
  );
}

/** Loading state with the shape of the content, not a spinner in the middle of nothing.
 *  The height is reserved so arriving content does not shove the page. */
function SectionSkeleton() {
  return (
    <div className={css.skeleton} role="status" aria-live="polite">
      <span className={css.srOnly}>Loading this section</span>
      <div className={css.skelBar} style={{ width: "38%" }} />
      <div className={css.skelBar} style={{ width: "62%" }} />
      <div className={css.skelPanel} />
    </div>
  );
}
