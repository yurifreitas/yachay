/** Types for the capability layer. Written by tools/capability_seed.py.
 *
 *  Costs are BANDS, never points, and the type enforces it: `capexUSD` is a tuple on an
 *  instrument and a {lo, hi} on a rolled-up plan. Anything that renders a single figure
 *  here is rendering a precision the data does not have.
 */
export type Money = { lo: number; hi: number };

export type Instrument = {
  id: string;
  name: string;
  klass: string;
  /** Why the measurement cannot be made another way. The load-bearing field. */
  physics: string;
  measures: string;
  limit: string;
  capexUSD: [number, number];
  opexUSDyr: number;
  sitingUSD: number;
  fte: number;
  roles: string[];
  /** Null only where no cheaper route exists — which is rarer than procurement suggests. */
  cheaperRoute: string | null;
};

export type Diagnostic = {
  catalogueName: string;
  standard: string;
  misses: string;
  sharper: string;
  instruments: string[];
  physics: string;
  perTestUSD: [number, number];
  changesManagement: string;
};

export type PlanStage = {
  name: string;
  does: string;
  needs: string[];
  gate: string;
};

export type Plan = {
  id: string;
  catalogueName: string;
  approach: string;
  goal: string;
  physics: string;
  stages: PlanStage[];
  instruments: string[];
  efficacy: string;
  efficacyEvidence: string;
  horizonYears: string;
  note: string;
  capexUSD: Money;
  opexUSDyr: number;
  sitingUSD: number;
  fte: number;
  roles: string[];
};

export type Capability = {
  generated: string;
  premise: string;
  provenance: string;
  instruments: Instrument[];
  diagnostics: Diagnostic[];
  plans: Plan[];
  summary: {
    instruments: number;
    byClass: Record<string, number>;
    withCheaperRoute: number;
    diagnostics: number;
    plans: number;
    planStages: number;
    byEfficacy: Record<string, number>;
    capexRangeUSD: Money;
    cheapestPlanUSD: number;
    dearestPlanUSD: number;
  };
};
