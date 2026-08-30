import { Suspense, lazy } from "react";










import { ConstraintPanel, ExpressionPanel, Form, VariantsPanel } from "./WorldPanels";
import { Needle, Pathways, Routes } from "./GeometryPanels";

import { RelatedGenes } from "./RelatedGenes";
import { Datasheet } from "./Datasheet";
import { Insights } from "./Insights";
import { Attention } from "./Attention";






const GeneLadder = lazy(() => import("./GeneLadder"));
import { Dependency, Cancer, Genotype, Network, Diseases } from "./genePanels";
import type { SectionRegistry } from "../../lib/sectionRegistry";

/** THE GENE PAGE'S SECTIONS, DECLARED — and every one of them given a sentence.
 *
 *  These seventeen were the barest of the three chains: `{section === "x" && <Panel/>}`, with
 *  no heading and no description at all. The rail's label was the only thing telling a reader
 *  what they were looking at, and a label is a name rather than a claim.
 *
 *  So each entry now carries a sentence, and the sentences are deliberately FACTUAL rather
 *  than interpretive: each says what the panel draws and which tool wrote the artefact behind
 *  it. That is checkable — a reader can open the named file — where an interpretation written
 *  by somebody who had not read the component would not be.
 *
 *  They keep `bare: true` because the panels draw their own frames, so the sentence is
 *  metadata the check can see rather than something rendered above them. Giving them a
 *  rendered heading would be a design change, and this commit is a move.
 */
export type GeneCtx = {
  rec: any;
  data: any;
  symbol: string;
  setSymbol: (s: string) => void;
  setQuery: (s: string) => void;
};

export const GENE_SECTIONS: SectionRegistry<GeneCtx> = [
  {
    id: "ladder",
    title: "",
    sub:
      "One gene across seven scales, with the measured cost of each step between two of them. Written by tools/gene_ladder.py; only two of the six transitions have a number behind them.",
    bare: true,
    view: (ctx) => (
      <><Suspense fallback={null}>
                  <GeneLadder gene={ctx.symbol || undefined} />
                </Suspense></>
    ),
  },
  {
    id: "datasheet",
    title: "",
    sub:
      "Every measured field this project holds for the gene, each with the artefact that produced it. Written by tools/gene_datasheet.py.",
    bare: true,
    view: (ctx) => (
      <><Datasheet rec={ctx.rec} /></>
    ),
  },
  {
    id: "attention",
    title: "",
    sub:
      "How much has been written about this gene against how much is known about it, with the catalogue-wide deciles beside it. Written by tools/gene_attention.py.",
    bare: true,
    view: (ctx) => (
      <><Attention rec={ctx.rec} scope={ctx.data.scope}
                           deciles={ctx.data.attDeciles ?? []}
                           caution={ctx.data.attCaution ?? ""}
                           baseline={ctx.data.attBaseline ?? ""}
                           onPick={(g) => { ctx.setSymbol(g); ctx.setQuery(""); }} /></>
    ),
  },
  {
    id: "insights",
    title: "",
    sub:
      "The read-outs this gene triggers, each with the rule that fired and the caution attached to it. Written by tools/gene_insights.py.",
    bare: true,
    view: (ctx) => (
      <><Insights found={ctx.rec?.ins} scope={ctx.data.scope}
                          rules={ctx.data.insRules ?? {}} caution={ctx.data.insCaution ?? ""} /></>
    ),
  },
  {
    id: "form",
    title: "",
    sub:
      "The protein as the public catalogues describe it — length, description, the UniProt record. Written by tools/gene_world.py.",
    bare: true,
    view: (ctx) => (
      <><Form world={ctx.rec?.world} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "constraint",
    title: "",
    sub:
      "gnomAD constraint: how much loss-of-function variation the population tolerates in this gene, against how much was expected. Written by tools/gene_world.py.",
    bare: true,
    view: (ctx) => (
      <><ConstraintPanel world={ctx.rec?.world} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "expression",
    title: "",
    sub:
      "Where the gene is expressed across the Human Protein Atlas cell types. Expression reachability, not cell biology. Written by tools/gene_world.py.",
    bare: true,
    view: (ctx) => (
      <><ExpressionPanel world={ctx.rec?.world} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "variants",
    title: "",
    sub:
      "The ClinVar picture for this gene: how many variants, and how much of it is uncertain significance. Written by tools/gene_world.py.",
    bare: true,
    view: (ctx) => (
      <><VariantsPanel world={ctx.rec?.world} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "needle",
    title: "",
    sub:
      "Where the variants fall along the protein, with the UniProt domains laid over the same axis. Written by tools/gene_geometry.py and tools/gene_domains.py.",
    bare: true,
    view: (ctx) => (
      <><Needle geo={ctx.rec?.geo} dom={ctx.rec?.dom} /></>
    ),
  },
  {
    id: "routes",
    title: "",
    sub:
      "The paths out of this gene to the rest of the atlas, each labelled with the relation it stands for. Written by tools/gene_geometry.py.",
    bare: true,
    view: (ctx) => (
      <><Routes geo={ctx.rec?.geo} /></>
    ),
  },
  {
    id: "pathways",
    title: "",
    sub:
      "The Reactome pathways this gene belongs to. A pathway is an inventory of reactions and a coarse one, which is why the ladder reports what the collapse costs.",
    bare: true,
    view: (ctx) => (
      <><Pathways geo={ctx.rec?.geo} /></>
    ),
  },
  {
    id: "dependency",
    title: "",
    sub:
      "What the DepMap screen says about this gene, calibrated against the null rather than read raw. Written by analyses/depmap_selective_dependency.py.",
    bare: true,
    view: (ctx) => (
      <><Dependency rec={ctx.rec} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "cancer",
    title: "",
    sub:
      "The same dependency, split by cancer subgroup, with the power to detect an effect reported before any p-value. Written by tools/cancer_subgroups.py.",
    bare: true,
    view: (ctx) => (
      <><Cancer rec={ctx.rec} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "genotype",
    title: "",
    sub:
      "Subgroups defined by genotype rather than by catalogue label, with the lineage and mutational-burden confounds measured instead of disclaimed. Written by tools/cancer_genotype.py.",
    bare: true,
    view: (ctx) => (
      <><Genotype rec={ctx.rec} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "network",
    title: "",
    sub:
      "This gene's neighbourhood in the interactome, against a degree-matched null so the hubs a random walk always finds are not mistaken for a finding.",
    bare: true,
    view: (ctx) => (
      <><Network rec={ctx.rec} scope={ctx.data.scope} /></>
    ),
  },
  {
    id: "disease",
    title: "",
    sub:
      "The diseases HPO assigns to this gene, and what the catalogue records about each.",
    bare: true,
    view: (ctx) => (
      <><Diseases rec={ctx.rec} /></>
    ),
  },
  {
    id: "related",
    title: "",
    sub:
      "Other genes reachable from this one, with the relation that connects them stated rather than implied. Written by tools/gene_related.py.",
    bare: true,
    view: (ctx) => (
      <><RelatedGenes rel={ctx.rec?.rel} onPick={(g) => { ctx.setSymbol(g); ctx.setQuery(""); }} /></>
    ),
  },
];
