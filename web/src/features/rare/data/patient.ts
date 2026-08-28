/** One dataset, one module — the code-split rule this feature follows. */
import rawFreq from "../../../data/generated/patient_frequencies.json";
import rawVariants from "../../../data/generated/patient_variants.json";
import rawClinvar from "../../../data/generated/clinvar_evidence.json";
import rawIntervals from "../../../data/generated/intervals.json";
import type { ClinvarEvidence, Intervals, PatientFrequencies } from "../patientModel";

export const patientFrequencies = rawFreq as unknown as PatientFrequencies;
export const clinvarEvidence = rawClinvar as unknown as ClinvarEvidence;
export const intervals = rawIntervals as unknown as Intervals;
export const patientVariants = rawVariants as unknown as {
  scale: { patients: number; variants: number; genes: number; diseases: number };
  allelicSpectrum: {
    genes: number; medianPrivateShare: number;
    genesWhereEveryVariantIsPrivate: number; shareOfGenesAllPrivate: number;
    top: { gene: string; patients: number; distinctVariants: number;
           privateShare: number; mostRecurrent: number }[];
  };
  consequences: Record<string, number>;
  zygosity: Record<string, number>;
  vitalStatusTrap: { deceased: number; aliveRecorded: number; warning: string };
};
