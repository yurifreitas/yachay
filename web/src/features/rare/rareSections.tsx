import { lazy } from "react";



import { type SortKey } from "./model";
import { GapMatrix } from "./components/GapMatrix";
import { OntologyLegend } from "./components/OntologyLegend";
import { DiseaseCard } from "./components/DiseaseCard";



import { TROP } from "../../i18n/tropical";
import { MEAS } from "../../i18n/measured";
import { MORE } from "../../i18n/more";
import { DEEP } from "../../i18n/deep";
import { SAMP } from "../../i18n/sampled";

import { StatusDot } from "../../components/atoms/StatusDot";
import { Chip } from "../../components/atoms/Chip";
import css from "./RarePage.module.css";
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
const ZAudit = lazy(() => import("./components/ZAudit").then((m) => ({ default: m.ZAudit })));
const CommunityStability = lazy(() => import("./components/CommunityStability").then((m) => ({ default: m.CommunityStability })));
const GeneEmbedding = lazy(() => import("./components/GeneEmbedding").then((m) => ({ default: m.GeneEmbedding })));
const GapPatterns = lazy(() => import("./components/GapPatterns").then((m) => ({ default: m.GapPatterns })));
const TropicalGap = lazy(() => import("./components/TropicalGap").then((m) => ({ default: m.TropicalGap })));
const ScaleLoss = lazy(() => import("./components/MeasuredPanels").then((m) => ({ default: m.ScaleLoss })));
const LanguageCoverage = lazy(() => import("./components/MeasuredPanels").then((m) => ({ default: m.LanguageCoverage })));
const ConflictContext = lazy(() => import("./components/MeasuredPanels").then((m) => ({ default: m.ConflictContext })));
const KnowledgeShape = lazy(() => import("./components/MeasuredPanels").then((m) => ({ default: m.KnowledgeShape })));
const GapTaxonomy = lazy(() => import("./components/MorePanels").then((m) => ({ default: m.GapTaxonomy })));
const HivResistance = lazy(() => import("./components/DeepPanels").then((m) => ({ default: m.HivResistance })));
const GeneConstraint = lazy(() => import("./components/DeepPanels").then((m) => ({ default: m.GeneConstraint })));
const SingleCellCoverage = lazy(() => import("./components/DeepPanels").then((m) => ({ default: m.SingleCellCoverage })));
const SampleAncestry = lazy(() => import("./components/SampledPanels").then((m) => ({ default: m.SampleAncestry })));
const SampleDisorders = lazy(() => import("./components/SampledPanels").then((m) => ({ default: m.SampleDisorders })));
const SampleJoins = lazy(() => import("./components/SampledPanels").then((m) => ({ default: m.SampleJoins })));
const TraitAxes = lazy(() => import("./components/TraitAtlas").then((m) => ({ default: m.TraitAxes })));
const TraitMatrix = lazy(() => import("./components/TraitAtlas").then((m) => ({ default: m.TraitMatrix })));
const SignalEnergy = lazy(() => import("./components/SignalEnergy").then((m) => ({ default: m.SignalEnergy })));
const TwinPropagation = lazy(() => import("./components/DeepPanels").then((m) => ({ default: m.TwinPropagation })));
const GenotypePhenotype = lazy(() => import("./components/DeepPanels").then((m) => ({ default: m.GenotypePhenotype })));
const AttentionBurden = lazy(() => import("./components/MorePanels").then((m) => ({ default: m.AttentionBurden })));
const AutismConvergence = lazy(() => import("./components/MorePanels").then((m) => ({ default: m.AutismConvergence })));
const VoidCells = lazy(() => import("./components/MorePanels").then((m) => ({ default: m.VoidCells })));
const PatientEvidence = lazy(() => import("./components/PatientEvidence").then((m) => ({ default: m.PatientEvidence })));
import type { SectionRegistry } from "../../lib/sectionRegistry";

/** THE RARE ATLAS'S SECTIONS, DECLARED.
 *
 *  Twenty-five branches, moved rather than rewritten: every title, sentence and view is the
 *  one that was in the render chain, lifted by a balanced-bracket walk so nested JSX could
 *  not be mis-cut, and diffed rather than retyped.
 *
 *  TWO CARRY `bare: true` because they draw their own frame — one opens with a warning
 *  banner, one splits into two blocks. Forcing them into heading-plus-view would have meant
 *  either rewriting working views or lying about what they are. They still declare a `sub`,
 *  so `web/scripts/check-sections.mjs` still sees them.
 *
 *  THE TRANSLATOR TRAVELS IN THE CONTEXT. `tt` is a hook result and a registry is a module,
 *  so the page passes it in rather than each view calling the hook — which keeps a section a
 *  value that can be listed, counted and checked instead of a component that must be mounted
 *  to find out what it is.
 *
 *  ADR 0009. The return is not the line count: a section in the rail with nothing to draw it
 *  is now a build failure instead of a blank panel.
 */
export type RareCtx = {
  tt: (b: any) => any;
  lexicon: any;
  ordered: any[];
  focus: any;
  sort: string;
  setSort: (s: any) => void;
  setSelected: (s: string | null) => void;
};

const SORTS: { id: SortKey; label: string }[] = [
  { id: "gaps", label: "Most unknown first" },
  { id: "rarity", label: "Rarest first" },
  { id: "name", label: "A–Z" },
];

export const RARE_SECTIONS: SectionRegistry<RareCtx> = [
  {
    id: "scale",
    title: (ctx) => (<>{ctx.tt(MEAS.scaleHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MEAS.scaleSub)}</>),
    view: () => (
      <><ScaleLoss /></>
    ),
  },
  {
    id: "language",
    title: (ctx) => (<>{ctx.tt(MEAS.langHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MEAS.langSub)}</>),
    view: () => (
      <><LanguageCoverage /></>
    ),
  },
  {
    id: "conflict",
    title: (ctx) => (<>{ctx.tt(MEAS.conflictHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MEAS.conflictSub)}</>),
    view: () => (
      <><ConflictContext /></>
    ),
  },
  {
    id: "shape",
    title: (ctx) => (<>{ctx.tt(MEAS.shapeHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MEAS.shapeSub)}</>),
    view: () => (
      <><KnowledgeShape /></>
    ),
  },
  {
    id: "gapkinds",
    title: (ctx) => (<>{ctx.tt(MORE.gapHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MORE.gapSub)}</>),
    view: () => (
      <><GapTaxonomy /></>
    ),
  },
  {
    id: "attention",
    title: (ctx) => (<>{ctx.tt(MORE.attHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MORE.attSub)}</>),
    view: () => (
      <><AttentionBurden /></>
    ),
  },
  {
    id: "autism",
    title: (ctx) => (<>{ctx.tt(MORE.autHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MORE.autSub)}</>),
    view: () => (
      <><AutismConvergence /></>
    ),
  },
  {
    id: "ancestrygwas",
    title: (ctx) => (<>{ctx.tt(SAMP.ancHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(SAMP.ancSub)}</>),
    view: () => (
      <><SampleAncestry /></>
    ),
  },
  {
    id: "disorders",
    title: (ctx) => (<>{ctx.tt(SAMP.disHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(SAMP.disSub)}</>),
    view: () => (
      <><SampleDisorders /></>
    ),
  },
  {
    id: "axes",
    title: (ctx) => (<>{ctx.tt(SAMP.pcpHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(SAMP.pcpSub)}</>),
    view: () => (
      <><TraitAxes /></>
    ),
  },
  {
    id: "grid",
    title: (ctx) => (<>{ctx.tt(SAMP.matHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(SAMP.matSub)}</>),
    view: () => (
      <><TraitMatrix /></>
    ),
  },
  {
    id: "signalenergy",
    title: (ctx) => (<>{ctx.tt(SAMP.seHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(SAMP.seSub)}</>),
    view: () => (
      <><SignalEnergy /></>
    ),
  },
  {
    id: "joins",
    title: (ctx) => (<>{ctx.tt(SAMP.joinHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(SAMP.joinSub)}</>),
    view: () => (
      <><SampleJoins /></>
    ),
  },
  {
    id: "cells",
    title: (ctx) => (<>{ctx.tt(DEEP.cellHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEEP.cellSub)}</>),
    view: () => (
      <><SingleCellCoverage /></>
    ),
  },
  {
    id: "constraint",
    title: (ctx) => (<>{ctx.tt(DEEP.conHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEEP.conSub)}</>),
    view: () => (
      <><GeneConstraint /></>
    ),
  },
  {
    id: "hiv",
    title: (ctx) => (<>{ctx.tt(DEEP.hivHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEEP.hivSub)}</>),
    view: () => (
      <><HivResistance /></>
    ),
  },
  {
    id: "twin",
    title: (ctx) => (<>{ctx.tt(DEEP.twinHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEEP.twinSub)}</>),
    view: () => (
      <><TwinPropagation /></>
    ),
  },
  {
    id: "genopheno",
    title: (ctx) => (<>{ctx.tt(DEEP.genoHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEEP.genoSub)}</>),
    view: () => (
      <><GenotypePhenotype /></>
    ),
  },
  {
    id: "voidcells",
    title: (ctx) => (<>{ctx.tt(MORE.voidHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(MORE.voidSub)}</>),
    view: () => (
      <><VoidCells /></>
    ),
  },
  {
    id: "tropical",
    title: (ctx) => (<>{ctx.tt(TROP.heading)}</>),
    sub: (ctx) => (<>{ctx.tt(TROP.sub)}</>),
    view: () => (
      <><TropicalGap /></>
    ),
  },
  {
    id: "gaps",
    title: <>The blanks are not scattered — they land on the same diseases</>,
    sub: <>The matrix on &ldquo;Where the data stops&rdquo; shows which fields are empty for
              one disease at a time, and structurally cannot show which are empty
              <em> together</em>. This counts the patterns over every OMIM-coded disease in the
              HPO annotation file. If the gaps were independent, most diseases with a gap would
              have exactly one; they do not.</>,
    view: () => (
      <><GapPatterns /></>
    ),
  },
  {
    id: "disease",
    title: <>One disease at a time, assembled from every source and nothing invented</>,
    sub: <>Genes, signs with their denominators, prevalence, onset, the cell types the
              genes reach, and what is being tried right now. No severity score — that would
              need a value judgement this project has no basis for.</>,
    view: () => (
      <><Dossier /></>
    ),
  },
  {
    id: "selfaudit",
    title: <>Twenty layers make overlapping claims. Nothing used to check whether they agree</>,
    sub: <>Every other section here reports a gap in somebody else&rsquo;s data. This one
              reports the gaps in ours: where two of our own layers contradict each other,
              whether the authored identifiers actually resolve against the catalogues, and
              what the field&rsquo;s evidence looks like when all 267,782 annotations are
              graded rather than twelve diseases. A dashboard that keeps its own
              contradictions in a file nobody opens is publishing them nowhere.</>,
    view: () => (
      <><SelfAudit /></>
    ),
  },
  {
    id: "zaudit",
    title: <>Every number here is a distance from a null. This is what those distances are worth</>,
    sub: <>The section above checks whether our layers agree with each other. This one checks
              whether our headline statistic can carry the weight put on it. It audits all
              3,166 published z values against the draw count of the null each was computed
              from &mdash; a permutation null of 200 draws resolves no tail below 1/201, so
              every z past about 2.6 is a distance measured against a spread and then extended
              along a curve nobody sampled. Two artefacts have a further problem: a null whose
              spread is under 1&thinsp;% of its own centre, which turns any deviation into an
              enormous number. The findings survive; the statistic that announced them does
              not, and both are said here.</>,
    view: () => (
      <><ZAudit /></>
    ),
  },
  {
    id: "cluster",
    title: <>Two thousand four hundred communities, from one run of one algorithm at one seed</>,
    sub: <>This site publishes a gene network partitioned into communities and never asked the
              partition a single question. It is asked three here. Run the same algorithm
              twelve times and the partitions agree at 0.90 &mdash; not 1, and as low as 0.79
              between one pair. Run a different algorithm and agreement falls to 0.29, so most
              of what separates these groupings is the objective function rather than the
              graph. Sweep the resolution twelvefold and the score moves by 0.03 while the
              largest community falls from 777 genes to 192, which means the resolution was
              never chosen by the data. What survives all of it is the membership:
              83&thinsp;% of the 3,335 scored genes sit with the same partners in at least
              nine runs of ten, and that number is now published per gene.</>,
    view: () => (
      <><CommunityStability /></>
    ),
  },
  {
    id: "embed",
    title: <>A UMAP is the most reproduced figure in biology and the least audited. Here is one, with its numbers</>,
    sub: <>Eleven measurements per gene, projected to two dimensions and clustered — the
              standard figure, built the standard way. Then the three questions its ubiquity
              has made unaskable. It keeps its local neighbourhoods well (0.945), and a third
              of every gene&rsquo;s neighbours still change when nothing changes but the random
              seed. Its clusters reproduce across seeds almost perfectly — and have essentially
              nothing to do with the clusters in the data they came from: HDBSCAN calls three
              quarters of these genes unclusterable noise in eleven dimensions and almost none
              of them on the picture. Reproducible is not correct, and this figure is both at
              once.</>,
    view: () => (
      <><GeneEmbedding /></>
    ),
  },
  {
    id: "patients",
    title: <>Ten thousand individual people, and what they say about the catalogue</>,
    sub: <>Every other section here reads an aggregate: it can say a disease involves
              seizures and that a gene has nonsense variants. This one reads 10,377 patients,
              and the difference is a denominator. Where the catalogue rests a frequency on
              <strong> one patient</strong> it reads 0.932 and the patients say 0.436 — a
              difference whose 95 % interval is nowhere near zero.</>,
    view: () => (
      <><PatientEvidence /></>
    ),
  },
  {
    id: "population",
    title: <>A prevalence is a property of a disorder <em>in a population</em>, and this
              catalogue records it as a scalar</>,
    sub: <>Orphanet stamps every prevalence record with a geography. Eleven analytical
              layers on this dashboard were built on that corpus and none of them had read
              the column. Reading it says that 73.5% of the disorders measured in more than
              one country disagree about which prevalence band they are in — and that the
              world&rsquo;s reference epidemiology is proportional to Europe, not to the
              world.</>,
    view: () => (
      <><Ancestry /></>
    ),
  },
  {
    id: "world",
    title: <>Every rare disease the field has catalogued, and where the data stops</>,
    sub: <>Joined from HPO, Orphanet and the Human Protein Atlas — not hand-written. The
              size is not the finding; how far the join gets before it runs out is.</>,
    view: () => (
      <><WorldAtlas /></>
    ),
  },
  {
    id: "capability",
    title: <>An approach is a room, an instrument, a physical limit and a payroll</>,
    sub: <>Every other tab says what is known. This one says what it would take: the
              instrument each stage is gated on, the physics that makes it unsubstitutable,
              the capital as a band rather than a figure, and the whole-time-equivalent staff
              — which is usually the column that is missing when a plan fails.</>,
    view: () => (
      <><Capability /></>
    ),
  },
  {
    id: "nongene",
    title: <>Every join on this site is keyed on a gene. This is what the key misses</>,
    sub: <>The atlas finds no causal gene for 3,801 of 14,831 diseases, and a disease
              without a gene is not merely missing a column — it is invisible to the cell
              axis, to the dependency screen and to every ranking here. So: when the causal
              unit is not a gene, what is it, and what fills each slot the gene fills?</>,
    view: () => (
      <><NonGene /></>
    ),
  },
  {
    id: "refmap",
    title: <>Eighty-four references, and the bridge they were supposed to demonstrate</>,
    sub: <>The map spans NF2 clinical work, gene therapy, rare-disease infrastructure,
              network biology, sparse HPC, tensor compilers and complex systems. Tagging each
              entry with its community and the ladder rung it serves turns the map into an
              audit — and the audit does not say what the map was assembled to say.</>,
    view: () => (
      <><References /></>
    ),
  },
  {
    id: "thesis",
    title: <>The argument these measurements serve, with its own register kept intact</>,
    sub: <>Every other section here is a measurement. This one is the thesis they were taken
              for — a ladder from genotype to patient, eighteen claims each marked as founded
              or hypothetical, and an audit of which of them this repository has actually
              built. Six are named and not built; three are absent. That is said at the same
              weight as the claims.</>,
    view: () => (
      <><Thesis /></>
    ),
  },
  {
    id: "dims",
    title: <>Seventeen people who changed how a field sees, each one actually run</>,
    sub: <>Each supplies a transform applied to the data already here. A name that yields
              no computation is marked as such rather than invoked — and the second group
              exists because the first one was all men, which was not an accident.</>,
    view: () => (
      <><Dimensions />
          <DimensionsTwo /></>
    ),
  },
  {
    id: "names",
    title: <>A name is upstream of every statistic on this page</>,
    sub: <>Etymology, the six naming eras still in simultaneous use, and what each name
              costs — including two that preserve a theory the field has abandoned and four
              withdrawn on ethical grounds.</>,
    view: () => (
      <><Nomenclature /></>
    ),
  },
  {
    id: "bias",
    title: <>Which numbers measure the world, and which measure who did the measuring</>,
    sub: <>A catalogue is a screen. This library's own argument applies to its own
              reference data — including one chart on the previous tab, and one sentence
              this dashboard had already published.</>,
    view: () => (
      <><BiasAudit /></>
    ),
  },
  {
    id: "choose",
    title: <>Which approach fits the programme you actually have</>,
    sub: <>Set your constraints on the left and your priorities below them. The model
              ranks the modalities and shows the contribution of every criterion, because a
              ranking without its decomposition is an opinion wearing a number.{" "}
              <strong>Not clinical guidance</strong> — a structured way to make assumptions
              explicit and disagree with them.</>,
    view: () => (
      <><ApproachChooser /></>
    ),
  },
  {
    id: "evidence",
    title: <>What a case series of four patients can actually support</>,
    sub: <>Ultra-rare literature is written in percentages drawn from single-digit series,
              and those percentages go on to shape registries, endpoints and n-of-1
              protocols. Set the two numbers that exist in the paper and read the three the
              paper does not print.</>,
    view: () => (
      <><EvidenceLab /></>
    ),
  },
  {
    id: "cell",
    title: <>Naming the gene rarely tells you what to do; naming the cell often does</>,
    sub: <>Lupus, as the disease that makes this repository's own premise clinical — and
              as the case that sits on the rare-disease boundary rather than inside or
              outside it.</>,
    view: () => (
      <><CellVsGene /></>
    ),
  },
  {
    id: "network",
    title: <>A network that grows, instead of a diagram that does not</>,
    sub: <>The real gene-gene graph — 5,524 genes, adjacent when they cause a common
              disease. Pick a seed, click to expand, double-click to add a second seed. The
              colour and the radius are a random walk with restart recomputed over whatever you
              have opened, so the picture is different every time because you built it.</>,
    view: () => (
      <><GrowingNetwork /></>
    ),
  },
  {
    id: "sparse",
    title: <>The same graph, as a sparse matrix, against its own null</>,
    sub: <>The reference audit found that the biological and computational literatures here
              never talk about the same object. This is that object, measured: modularity,
              degree skew, and whether reordering by biological community improves memory
              locality more than it does on a rewiring with the identical degree sequence.</>,
    view: () => (
      <><SparseStructure /></>
    ),
  },
  {
    id: "atlas",
    title: "",
    sub: "This section draws its own frame — see the view.",
    bare: true,
    view: (ctx) => (
      <><>
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
                {SORTS.map((o: any) => (
                  <button
                    key={o.id}
                    type="button"
                    className={ctx.sort === o.id ? css.tabOn : css.tab}
                    aria-pressed={ctx.sort === o.id}
                    onClick={() => ctx.setSort(o.id)}
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

            <GapMatrix lexicon={ctx.lexicon} diseases={ctx.ordered} />
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
                {ctx.ordered.slice(0, 6).map((d: any) => (
                  <button
                    key={d.name}
                    type="button"
                    className={ctx.focus?.name === d.name ? css.tabOn : css.tab}
                    aria-pressed={ctx.focus?.name === d.name}
                    onClick={() => ctx.setSelected(d.name)}
                  >
                    {d.name.length > 26 ? d.name.slice(0, 24) + "\u2026" : d.name}
                  </button>
                ))}
              </div>
            </div>
            {ctx.focus && <DiseaseCard d={ctx.focus} />}
          </section>
        </></>
    ),
  },
  {
    id: "sources",
    title: "",
    sub: "This section draws its own frame — see the view.",
    bare: true,
    view: (ctx) => (
      <><>
          <div className={css.warn} role="note">
            <strong>This is a schema demonstration, not a reference database.</strong>{" "}
            {ctx.lexicon.provenance}
          </div>

          <section className={css.block}>
            <h3 className={css.h3}>Six systems index the same disease, and none is a superset of the others</h3>
            <p className={css.sub}>
              Each was built for a different job. MONDO exists specifically to merge them,
              which is the clearest statement that the fragmentation is real.
            </p>
            <OntologyLegend ontologies={ctx.lexicon.ontologies} />
          </section>

          <section className={css.block}>
            <h3 className={css.h3}>&ldquo;Rare&rdquo; is not one definition</h3>
            <p className={css.sub}>
              The threshold is set by jurisdiction, and two of the four are absolute counts
              rather than rates — so whether a disease is rare depends on where the patient
              lives and how many people live there.
            </p>
            <div className={css.defs}>
              {ctx.lexicon.definitions.map((d: any) => (
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
              {ctx.lexicon.fieldFacts.map((f: any) => (
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
        </></>
    ),
  },
];
