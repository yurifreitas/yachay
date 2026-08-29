/** The multiscale ladder, in both languages.
 *
 *  The argument this component makes is that the STEPS between scales are not free, and that
 *  most of them have never been measured. The Portuguese says that as directly as the
 *  English, because a reader who misses it takes the ladder for a finished model.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const LADDER = {
  pick: bi("Gene", "Gene"),
  lede1: bi(
    "Every multiscale figure in biology draws this ladder and implies the steps are free.",
    "Toda figura multiescala em biologia desenha esta escada e sugere que os degraus são de graça.",
  ),
  lede2: bi(
    "They are not. Each connector below carries what the step costs — or says plainly that "
    + "nobody has measured it. Measured:",
    "Não são. Cada conector abaixo carrega o que o degrau custa — ou diz na cara que ninguém "
    + "mediu. Medidos:",
  ),
  ofSix: bi("of 6", "de 6"),
  kept: bi("kept", "guardado"),
  notMeasured: bi("not measured", "não medido"),

  rResidue: bi("Residue · variants along the protein",
               "Resíduo · variantes ao longo da proteína"),
  rProtein: bi("Protein", "Proteína"),
  rInteraction: bi("Interaction · STRING ≥ 700", "Interação · STRING ≥ 700"),
  rPathway: bi("Pathway · Reactome top level", "Via · topo do Reactome"),
  rCell: bi("Cell type · Human Protein Atlas", "Tipo celular · Human Protein Atlas"),
  rSystem: bi("Organ system · via this gene's diseases",
              "Sistema orgânico · via as doenças deste gene"),

  around: bi("around residue", "em torno do resíduo"),
  residues: bi("residues", "resíduos"),
  features: bi("annotated features", "elementos anotados"),
  placed: bi("variants placed", "variantes posicionadas"),
  noPathway: bi("no Reactome top-level pathway reaches this gene",
                "nenhuma via de topo do Reactome alcança este gene"),
  retentionTip: bi("what a pathway collapse keeps for this organ system",
                   "o que um colapso em vias guarda para este sistema orgânico"),
  systemNote: bi(
    "The percentage on a system is what collapsing genes onto pathways keeps for it — 0.39 "
    + "for neoplasm, 0.07 for cardiovascular. It is a property of the SYSTEM, not of this gene.",
    "A porcentagem num sistema é o que colapsar genes em vias guarda para ele — 0,39 para "
    + "neoplasia, 0,07 para cardiovascular. É propriedade do SISTEMA, não deste gene.",
  ),
} as const;
