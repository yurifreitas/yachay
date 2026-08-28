/** Types for the measured half of the non-gene layer. Written by tools/nongene_measure.py.
 *
 *  Nothing here is authored except the mapping from an HPO term to a seed class, which the
 *  tool carries in one dictionary so it can be argued with in one place.
 */
export type VocabTerm = {
  term: string; name: string; diseases: number;
  mendelian: boolean; seedClass: string | null;
};

export type MeasuredClass = {
  seedClass: string; diseases: number;
  terms: { term: string; name: string }[];
  withGene: number; geneLess: number; examples: string[];
};

export type Unmeasurable = { seedClass: string; diseases: number; why: string };

export type NonGeneMeasured = {
  generated: string;
  inputs: string[];
  premise: string;
  scale: {
    diseasesAnnotated: number; withInheritanceAnnotation: number;
    withGene: number; geneLess: number;
  };
  vocabulary: VocabTerm[];
  measured: MeasuredClass[];
  unmeasurable: Unmeasurable[];
  geneLessBreakdown: {
    total: number; withAnyInheritance: number; withMendelianInheritance: number;
    withNonMendelianInheritance: number; withNoInheritanceAnnotation: number; says: string;
  };
  finding: string;
  summary: {
    vocabularyTerms: number; nonMendelianTerms: number;
    classesWithFootprint: number; classesWithNoVocabulary: number;
  };
};
