/** What the public catalogues hold about a gene, typed.
 *
 *  Written by `tools/gene_world.py` from four files that were on disk and had never been
 *  read per gene: STRING protein annotations, gnomAD v4.1 constraint, the Human Protein
 *  Atlas single-cell matrix, and ClinVar.
 */

export type ProteinInfo = {
  /** Residues. A length is the crudest possible description of form, and it is still the
   *  first thing that separates a 76-residue ubiquitin from a 34,350-residue titin. */
  size: number | null;
  note: string;
};

export type Constraint = {
  /** The upper bound of observed/expected loss-of-function. gnomAD's own recommended
   *  ranking statistic; below ~0.35 is the constrained end. Null when the gene is too
   *  short for the bound to mean anything, which is the honest outcome. */
  loeuf: number | null;
  oe: number | null;
  pLI: number | null;
  misZ: number | null;
  lofObs: number;
  lofExp: number;
  mane: boolean;
};

export type Expression = {
  top: { cell: string; nCPM: number }[];
  /** How many cell types carry it above the stated floor. Three and seventy-eight are
   *  different kinds of gene, and a therapy aimed at the second has nowhere to hide. */
  typesAbove: number;
};

export type ClinVarCounts = {
  total: number;
  pathogenic: number;
  benign: number;
  uncertain: number;
  conflicting: number;
  other: number;
  /** Share of submitted variants nobody could classify. A measurement of attention, not of
   *  the gene — see the panel's own note. */
  vusShare: number;
};

export type WorldRecord = {
  prot?: ProteinInfo;
  con?: Constraint;
  exp?: Expression;
  clin?: ClinVarCounts;
};

export type GeneWorld = {
  generated: string;
  premise: string;
  scope: {
    protein: { proteins: number; source?: string; note?: string };
    constraint: { genes: number; source?: string; note?: string };
    expression: { genes: number; cellTypes?: number; floor?: number; source?: string };
    clinvar: { genes: number; rows?: number; assembly?: string; source?: string };
    genes: number;
  };
  genes: Record<string, WorldRecord>;
};

/** Where a LOEUF sits, in words a reader can act on.
 *
 *  The bands are gnomAD's own guidance and not a scale invented here: the first LOEUF decile
 *  is the constrained set the consortium recommends prioritising, and 1.0 is the value a gene
 *  under no measurable constraint would show. The label never says "pathogenic" — constraint
 *  is a population-genetic observation and reading it as disease evidence is the commonest
 *  misuse of the file.
 */
export function loeufBand(loeuf: number | null): "constrained" | "middling" | "tolerant" | null {
  if (loeuf == null) return null;
  if (loeuf < 0.35) return "constrained";
  if (loeuf < 1.0) return "middling";
  return "tolerant";
}

/** Whether a VUS share is worth remarking on, given how many variants it rests on.
 *
 *  A 100 % VUS share over three variants is noise; over three thousand it is a statement
 *  about a field. The threshold is stated rather than hidden so a reader can disagree with
 *  it — which is the whole difference between a gate and an opinion.
 */
export const VUS_MIN_VARIANTS = 20;

export function vusIsMeaningful(c: ClinVarCounts | undefined): boolean {
  return !!c && c.total >= VUS_MIN_VARIANTS;
}
