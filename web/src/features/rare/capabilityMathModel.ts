/** Types for the derived arithmetic. Written by tools/capability_math.py.
 *  Every field here is computed from capability.json and dossiers.json — none is authored,
 *  which is why the model carries no free-text judgement fields except the stated assumptions.
 */
import type { Money } from "./capabilityModel";

/** The high end can be unbounded: a class of "<1 / 1 000 000" has a true floor of zero, so
 *  dividing by it has no answer. Null means unbounded, never zero. */
export type OpenMoney = { lo: number; hi: number | null };

export type PerPatient = {
  planId: string; catalogueName: string; approach: string;
  prevalenceClass: string | null;
  capexUSD: Money;
  trials: number | null;
  patients: Money | null;
  patientsEurope: Money | null;
  capitalPerPatientUSD: OpenMoney | null;
  orpha: string | null;
  cohortBasis: string;
  prevalenceRecords: number | null;
  typesPresent: string[];
  stringCohort: Money | null;
  stringCapitalPerPatientUSD: Money | null;
};

/** How far the audited cohort moved the answer, per disease and per end of the band. */
export type Movement = {
  catalogueName: string;
  fromUSD: Money; toUSD: OpenMoney;
  fromCohort: Money | null; toCohort: Money | null;
  folds: { lo?: number; hi?: number };
  biggestFold: number;
  basis: string;
  records: number | null;
};

export type SharedInstrument = {
  id: string; name: string; plans: number; diseases: string[];
  capexUSD: [number, number]; wastedIfNotSharedUSD: Money;
};

export type QueueRow = {
  id: string; name: string; unit: string; throughputPerYear: number;
  instrumentYears: number; instrumentsForOneYear: number; consumablesForCohortUSD: number;
};

export type Queue = {
  planId: string; catalogueName: string; cohort: number;
  rows: QueueRow[]; bottleneck: string; bottleneckYears: number;
};

export type Inversion = {
  id: string; name: string; unit: string;
  capexUSD: [number, number]; costPerAnswerUSD: number;
  rankByCapital: number; rankByAnswer: number; move: number;
};

export type Discrepancy = {
  catalogueName: string; readAs: string | null;
  conflictsWith: string; likelyCause: string; effect: string;
};

export type CapabilityMath = {
  generated: string;
  inputs: string[];
  premise: string;
  assumptions: Record<string, string | number>;
  discrepancies: Discrepancy[];
  cohortSource: string;
  movement: Movement[];
  finding: string;
  capitalPerPatient: PerPatient[];
  sharing: {
    sumOfPlansUSD: Money; unionOfInstrumentsUSD: Money; doubleCountedUSD: Money;
    doubleCountedFraction: number; distinctInstruments: number;
    instrumentSlotsAcrossPlans: number; byInstrument: SharedInstrument[];
  };
  queue: Queue[];
  capitalVsAnswer: Inversion[];
  summary: {
    plansWithPrevalence: number;
    capitalPerPatientRangeUSD: { lowest: number | null; highest: number | null };
    cheapestDisease: string | null; dearestDisease: string | null;
    biggestRankMove: string | null; biggestRankMoveBy: number | null;
  };
};
