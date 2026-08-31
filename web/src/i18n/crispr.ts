/** The three hyperdimensional views of the DepMap run, in both languages.
 *
 *  These carry the library's central claim, so the Portuguese is the argument rather than a
 *  translation of it: a raw score is not comparable across genes measured different numbers
 *  of times, and the maximum of that metric is toxicity.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const CRISPR = {
  fieldTitle: bi("The same score is a different result at a different n.",
                 "O mesmo escore é um resultado diferente com um n diferente."),
  fieldHint: bi("hover a cell — the ring marks where pan-essential genes concentrate",
                "passe por uma célula — o anel marca onde os genes pan-essenciais se concentram"),
  rawScore: bi("raw score", "escore bruto"),
  lines: bi("cell lines", "linhagens"),
  genes: bi("genes", "genes"),
  around: bi("around score", "em torno do escore"),
  keyGenes: bi("genes land here", "genes caem aqui"),
  keyEssential: bi("pan-essential concentrate here — toxicity, not selectivity",
                   "pan-essenciais se concentram aqui — toxicidade, não seletividade"),

  bumpTitle: bi("What calibration moved, and what it moved out.",
                "O que a calibração moveu, e o que ela tirou."),
  rawRank: bi("raw rank", "posição bruta"),
  calRank: bi("calibrated rank", "posição calibrada"),
  bumpHint1: bi("of the raw top 60 are pan-essential", "dos 60 primeiros brutos são pan-essenciais"),
  bumpHint2: bi("fell after calibration", "caíram após a calibração"),
  bumpHint3: bi("of those that fell are pan-essential", "dos que caíram são pan-essenciais"),

  matrixTitle: bi("Which dependencies belong to one lineage, and which the metric likes everywhere.",
                  "Quais dependências pertencem a uma linhagem, e quais a métrica gosta em toda parte."),
  matrixHint: bi("genes were nominated by more than one lineage, of",
                 "genes foram indicados por mais de uma linhagem, de"),
  inLineage: bi("in", "em"),
  nominatedBy: bi("nominated by lineages:", "indicado por linhagens:"),

  /* The figure that replaced one that did not work. */
  sEvent: bi("The three populations", "As três populações"),
  eventTitle: bi(
    "where the controls sit is what the calibration is judged on",
    "onde os controles caem é o que julga a calibração",
  ),
  eventSub: bi(
    "A screen contains three populations: common-essential genes, which are the confound "
    + "Stage 3 removes; nonessential controls, designed to be inert; and everything else, "
    + "which is the candidate pool. This draws all three against the null's own percentiles, "
    + "ordered by median. It replaced a figure that could not be drawn, and says why.",
    "Uma triagem contém três populações: genes comumente essenciais, que são o confundidor "
    + "que o Estágio 3 remove; controles não essenciais, feitos para serem inertes; e todo o "
    + "resto, que é o conjunto de candidatos. Isto desenha as três contra os percentis do "
    + "próprio nulo, ordenadas pela mediana. Substituiu uma figura que não pôde ser "
    + "desenhada, e diz por quê.",
  ),
  eventRules: bi("which null percentile to emphasise",
                 "qual percentil do nulo destacar"),

  /* ---- the whole matrix, drawn ------------------------------------------------------
     Added beside the run-dashboard strings rather than in a new module: they are the same
     dataset, and a second file called `crispr` is how one of them gets overwritten. */
  wholeTitle: bi("The whole screen", "A triagem inteira"),
  wholeLoading: bi("fetching 21 million measurements…",
                    "buscando 21 milhões de medições…"),
  wholeMargin: bi(
    "share of each column that is a known common-essential gene",
    "fração de cada coluna que é um gene essencial comum conhecido",
  ),
  wholeOrderingK: bi("the ordering, and what it cannot do",
                      "a ordenação, e o que ela não consegue"),
  wholeRoughnessK: bi("whether the ordering earns its place",
                       "se a ordenação merece o lugar dela"),
  wholeBinningK: bi("what a column is", "o que é uma coluna"),
  wholeSeriated: bi("seriated", "seriada"),
  wholeAlpha: bi("alphabetical — the control", "alfabética — o controle"),
  wholeShuffled: bi("shuffled — no ordering at all", "embaralhada — ordenação nenhuma"),
} as const;
