/** Three measurements that reached no delivery path, in both languages.
 *
 *  Found by `scripts/check-artefacts.mjs` rather than by reading: one of them applies this
 *  method outside rare disease entirely, one is the rung the repository's own ladder grades
 *  as built, and one reports that 470 of its 510 tests could not have detected the effect
 *  they were asked about. That last one is the most useful number here and it was in a file
 *  nobody opened.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const DEEP = {
  // ---------------------------------------------------------------- beyond rare disease
  gBeyond: bi("Beyond rare disease", "Fora da doença rara"),
  qBeyond: bi(
    "The same method on a domain that did not produce it — and what that domain breaks.",
    "O mesmo método num domínio que não o produziu — e o que esse domínio quebra.",
  ),
  sHiv: bi("HIV drug resistance", "Resistência do HIV"),
  hivHeading: bi(
    "the positive controls were named before the run, and they came back",
    "os controles positivos foram nomeados antes da execução, e voltaram",
  ),
  hivSub: bi(
    "Three drug panels, 1,009 mutations scored against a permutation null. The known "
    + "resistance mutations were written down from the literature first and then recovered: "
    + "6 of 7, 6 of 7, 5 of 5. A shortlist whose positive control fails is blocked, so the "
    + "control is what makes the rest of the table readable.",
    "Três painéis de fármacos, 1.009 mutações pontuadas contra um nulo de permutação. As "
    + "mutações de resistência conhecidas foram escritas a partir da literatura primeiro e "
    + "depois recuperadas: 6 de 7, 6 de 7, 5 de 5. Uma lista cujo controle positivo falha "
    + "fica bloqueada, então é o controle que torna o resto da tabela legível.",
  ),
  hivBreaks: bi("what this domain breaks in the method",
                "o que este domínio quebra no método"),
  hivPanels: bi("three panels, each with its own null",
                "três painéis, cada um com seu nulo"),
  hivPassengers: bi("and the entries the adapter predicted would be passengers",
                    "e as entradas que o adaptador previu como caronas"),

  // ---------------------------------------------------------------- propagation
  sTwin: bi("Propagation from the seeds", "Propagação a partir das sementes"),
  twinHeading: bi(
    "a walk from any seed finds hubs, so every value here is a z against degree",
    "uma caminhada a partir de qualquer semente encontra hubs, então todo valor aqui é um z contra o grau",
  ),
  twinSub: bi(
    "Random walk with restart over 16,201 proteins and 236,930 edges, from the causal genes "
    + "of eleven disorders. Reported against 200 degree-stratified seed sets per target, "
    + "never as a raw score — a propagation without a degree-matched null is a list of the "
    + "best-connected proteins in the graph.",
    "Caminhada aleatória com reinício sobre 16.201 proteínas e 236.930 arestas, a partir dos "
    + "genes causais de onze distúrbios. Reportado contra 200 conjuntos de sementes "
    + "estratificados por grau, nunca como escore bruto — uma propagação sem nulo pareado "
    + "por grau é uma lista das proteínas mais conectadas do grafo.",
  ),
  twinIsNot: bi("what this is not", "o que isto não é"),
  twinLadder: bi("the rung this moves, and the ones it does not",
                 "o degrau que isto move, e os que não"),

  // ---------------------------------------------------------------- power
  sGeno: bi("Truncating versus missense", "Truncante versus missense"),
  genoHeading: bi(
    "470 of 510 tests could not have found the effect they were asked about",
    "470 de 510 testes não poderiam ter encontrado o efeito sobre o qual foram perguntados",
  ),
  genoSub: bi(
    "Patient-level phenopackets, asking whether the patients with loss-of-function variants "
    + "differ in a feature from those with missense. The power model is reported before the "
    + "hits, because a null result from an underpowered test is not a null result.",
    "Fenopacotes em nível de paciente, perguntando se os pacientes com variantes de perda de "
    + "função diferem em alguma característica dos que têm missense. O modelo de poder vem "
    + "antes dos achados, porque um resultado nulo de um teste sem poder não é um resultado nulo.",
  ),
  genoPower: bi("what the design could and could not see",
                "o que o desenho podia e não podia ver"),
  genoHits: bi("the six that survived correction", "os seis que sobreviveram à correção"),
  genoSkipped: bi("patients the design excluded, and why",
                  "pacientes que o desenho excluiu, e por quê"),
} as const;
