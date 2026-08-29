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
} as const;
