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
  compositionK: bi(
    "the full composition, not just the disorder share",
    "a composição inteira, não só a fração de transtorno",
  ),
  compositionNote: bi(
    "Weighted by sample. `unclassified` is published rather than folded into the others to "
    + "make the bar look complete — it is what no rule matched, and hiding it would be the "
    + "one edit that makes this figure dishonest.",
    "Ponderado por amostra. `unclassified` é publicado em vez de dissolvido nos outros para a "
    + "barra parecer completa — é o que nenhuma regra pegou, e escondê-lo seria a única edição "
    + "que tornaria esta figura desonesta.",
  ),
  kDisorder: bi("disorder", "transtorno"),
  kQuantity: bi("quantity", "quantidade"),
  kConsequence: bi("organ consequence", "consequência de órgão"),
  kCessation: bi("cessation", "cessação"),
  kResponse: bi("response", "resposta"),
  kUnclassified: bi("unclassified", "não classificado"),
  studiesDisorder: bi("studies are of a disorder", "estudos são de transtorno"),
  ancestryK: bi(
    "and who was sequenced, which differs by substance for a reason",
    "e quem foi sequenciado, que difere por substância por um motivo",
  ),
  ancestryNote: bi(
    "Each analysis counts once, split across the ancestries it reports; summing people would "
    + "count the same cohort once per study. And the number worth stopping on is alcohol's: "
    + "8.8 % East Asian, among the LOWEST of any substance here — while the best-established "
    + "protective variants in alcohol genetics, ALDH2*2 and ADH1B*2, are essentially "
    + "East-Asian-specific. The field's clearest protective biology comes from the population "
    + "its samples least represent. Stimulants, at 37.5 % East Asian and 38 % European, are "
    + "the least European-dominated substance in the table and also the smallest by three "
    + "orders of magnitude.",
    "Cada análise conta uma vez, dividida entre as ancestralidades que reporta; somar pessoas "
    + "contaria a mesma coorte uma vez por estudo. E o número em que vale parar é o do álcool: "
    + "8,8 % do Leste Asiático, um dos MAIS BAIXOS de qualquer substância aqui — enquanto as "
    + "variantes protetoras mais bem estabelecidas na genética do álcool, ALDH2*2 e ADH1B*2, "
    + "são essencialmente específicas do Leste Asiático. A biologia protetora mais clara do "
    + "campo vem da população que suas amostras menos representam. Estimulantes, com 37,5 % do "
    + "Leste Asiático e 38 % europeu, são a substância menos dominada por europeus da tabela — "
    + "e também a menor, por três ordens de grandeza.",
  ),
  european: bi("European", "europeu"),
  africanMajority: bi("African-majority analyses", "análises de maioria africana"),
  genes: bi("genes", "genes"),
  cellType: bi("cell type", "tipo celular"),
  genesIn: bi("genes", "genes"),
  expected: bi("expected", "esperado"),
  fold: bi("fold", "vezes"),
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
