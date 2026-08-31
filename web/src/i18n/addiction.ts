/** Substance use: what the genetics of it actually measured. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const ADD = {
  title: bi(
    "Addiction, and what its genetics measured",
    "Vício, e o que a genética dele mediu",
  ),
  blurb: bi(
    "Three questions under one heading: who cannot stop, who uses a lot, and whose organs "
    + "fail. The share of sample behind each.",
    "Três perguntas sob um título só: quem não consegue parar, quem usa muito, e quem tem "
    + "os órgãos falhando. A fração de amostra atrás de cada uma.",
  ),
  bySubstance: bi(
    "how much of each substance's genetics is about a disorder at all",
    "quanto da genética de cada substância é sobre um transtorno, afinal",
  ),
  scaleK: bi(
    "and the scale each substance was studied at",
    "e a escala em que cada substância foi estudada",
  ),
  studies: bi("studies", "estudos"),
  cellsK: bi(
    "and whether the two land in the same cells",
    "e se as duas aterrissam nas mesmas células",
  ),
  disorderCells: bi("disorder phenotypes", "fenótipos de transtorno"),
  quantityCells: bi("quantity phenotypes", "fenótipos de quantidade"),
  shared: bi("shared:", "em comum:"),
  noneSurvive: bi("nothing survives correction", "nada sobrevive à correção"),
  filterK: bi(
    "what was thrown out, and what could not be classified",
    "o que foi descartado, e o que não deu para classificar",
  ),
  excluded: bi(
    "accessions that mention a substance without being about it — smoking as a covariate on "
    + "arthritis, alcohol dehydrogenase assays",
    "acessos que citam uma substância sem serem sobre ela — fumo como covariável em artrite, "
    + "ensaios de álcool-desidrogenase",
  ),
  unclassified: bi(
    "accessions no rule matched, counted rather than dropped",
    "acessos que nenhuma regra pegou, contados em vez de descartados",
  ),
  fitK: bi("what this is not", "o que isto não é"),
} as const;
