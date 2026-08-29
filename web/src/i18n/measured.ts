/** The ADR 0007 layer, in both languages.
 *
 *  These four sections are the only results on this site that carry a governing decision
 *  record, a null, an interval and a registered drift check. The Portuguese is written as
 *  the argument rather than as a translation of it — and one of these sections says, in
 *  both languages, that its own hypothesis failed.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const MEAS = {
  group: bi("What was measured", "O que foi medido"),
  question: bi(
    "Four ideas, each with a null and an interval — and one that did not survive",
    "Quatro ideias, cada uma com nulo e intervalo — e uma que não sobreviveu",
  ),

  // --------------------------------------------------------------- scale
  sScale: bi("What a change of scale costs", "O que custa mudar de escala"),
  scaleHeading: bi(
    "Collapsing genes onto pathways keeps a fifth of what they said",
    "Colapsar genes em vias guarda um quinto do que eles diziam",
  ),
  scaleSub: bi(
    "A disease is described by its causal genes. Collapse those genes onto a coarser "
    + "alphabet — the 29 Reactome top-level pathways, or the 154 cell types where they are "
    + "expressed — and ask how much of what they said about the disease's organ systems "
    + "survives. Every figure is the excess over a permutation null, because mutual "
    + "information rises with alphabet size for free.",
    "Uma doença é descrita pelos seus genes causais. Colapse esses genes num alfabeto mais "
    + "grosso — as 29 vias de topo do Reactome, ou os 154 tipos celulares onde eles se "
    + "expressam — e pergunte quanto do que eles diziam sobre os sistemas orgânicos da "
    + "doença sobrevive. Todo número é o excesso sobre um nulo de permutação, porque "
    + "informação mútua cresce com o tamanho do alfabeto de graça.",
  ),
  scaleRetained: bi("kept, at 181-fold compression", "guardado, a 181× de compressão"),
  scaleSpread: bi(
    "And the loss is concentrated, not uniform. Pathways hold what is pathway-shaped and "
    + "lose what is structural — which is why there is no single right scale for this atlas.",
    "E a perda é concentrada, não uniforme. As vias guardam o que tem forma de via e perdem "
    + "o que é estrutural — por isso não existe uma escala certa única para este atlas.",
  ),
  scaleDirection: bi("The relation has a direction", "A relação tem direção"),
  scaleDirectionSub: bi(
    "Genes predict organ system far better than organ system predicts genes — and the "
    + "asymmetry collapses under compression. The summary destroyed the direction, not only "
    + "the magnitude.",
    "Genes preveem sistema orgânico muito melhor que sistema orgânico prevê genes — e a "
    + "assimetria colapsa sob compressão. O resumo destruiu a direção, não só a magnitude.",
  ),

  // --------------------------------------------------------------- language
  sLang: bi("What a reader loses", "O que o leitor perde"),
  langHeading: bi(
    "This page exists in Portuguese. The phenotype behind it mostly does not",
    "Esta página existe em português. O fenótipo por trás dela, em boa parte, não",
  ),
  langSub: bi(
    "HPO ships fourteen language profiles besides English. Weighted by the annotations "
    + "diseases actually carry — not by how many terms a project has translated — coverage "
    + "runs from complete to zero.",
    "O HPO publica catorze perfis de idioma além do inglês. Ponderado pelas anotações que as "
    + "doenças de fato carregam — e não por quantos termos um projeto traduziu — a cobertura "
    + "vai de completa a zero.",
  ),
  langSpread: bi(
    "spread across organ systems, for Portuguese",
    "de espalhamento entre sistemas orgânicos, no português",
  ),
  langWorst: bi("weakest system", "sistema mais fraco"),
  langBest: bi("strongest system", "sistema mais forte"),
  langNote: bi(
    "Translators went for the terms that matter first: French covers 69 % of the vocabulary "
    + "and 98 % of the annotation mass. A progress report counting terms cannot show that — "
    + "and cannot show the hole in Portuguese either.",
    "Os tradutores foram primeiro nos termos que importam: o francês cobre 69 % do "
    + "vocabulário e 98 % da massa de anotação. Um relatório de progresso que conta termos "
    + "não mostra isso — nem mostra o buraco no português.",
  ),
  langTerms: bi("of the vocabulary", "do vocabulário"),
  langAnnot: bi("of what diseases are annotated with", "do que as doenças carregam"),

  // --------------------------------------------------------------- conflict
  sConflict: bi("Conflict, or context?", "Conflito, ou contexto?"),
  conflictHeading: bi(
    "About half of recorded scientific disagreement is not disagreement",
    "Cerca de metade da discordância científica registrada não é discordância",
  ),
  conflictSub: bi(
    "ClinVar marks 165,843 variants as carrying conflicting classifications. Reading the "
    + "6.4 million individual submissions — each with the condition it was made against — "
    + "splits them in two: submitters who disagree about the SAME condition, and submitters "
    + "who never disagree at all until their conditions are pooled into one column.",
    "O ClinVar marca 165.843 variantes como tendo classificações conflitantes. Lendo as 6,4 "
    + "milhões de submissões individuais — cada uma com a condição contra a qual foi feita — "
    + "elas se partem em duas: quem discorda sobre a MESMA condição, e quem nunca discorda de "
    + "fato até que as condições sejam jogadas na mesma coluna.",
  ),
  conflictAcross: bi("context — every condition internally consistent",
                     "contexto — toda condição internamente consistente"),
  conflictWithin: bi("contradiction — somebody is wrong",
                     "contradição — alguém está errado"),
  conflictSens: bi(
    "Removing the three panel indications takes the context share to 48.6 %. Granularity is "
    + "worth about nine points; roughly half the corpus is context under either reading.",
    "Removendo as três indicações de painel, a fração de contexto cai para 48,6 %. "
    + "Granularidade vale uns nove pontos; cerca de metade do corpus é contexto nas duas "
    + "leituras.",
  ),
  conflictRedundancy: bi(
    "And more reviewers do not settle it: with the condition held fixed, internal "
    + "disagreement rises to about a quarter by the third submitter and stays there through "
    + "the eleventh. An aggregate classification is not a consensus.",
    "E mais revisores não resolvem: com a condição fixa, a discordância interna sobe para "
    + "cerca de um quarto já no terceiro submissor e fica lá até o décimo primeiro. Uma "
    + "classificação agregada não é um consenso.",
  ),

  // --------------------------------------------------------------- shape
  sShape: bi("The idea that failed", "A ideia que falhou"),
  shapeHeading: bi(
    "Knowledge was supposed to have a shape. It mostly has a registry",
    "O conhecimento deveria ter uma forma. Ele tem, na maior parte, um registro",
  ),
  shapeSub: bi(
    "The proposal was that what matters is not how much is known about a disease but the "
    + "shape of it — bright on genetics, dark on natural history. Measured across five axes, "
    + "the prediction fails: knowledge is LESS concentrated than independence would give, and "
    + "the statistic turns out to track how many axes are populated rather than their shape.",
    "A proposta era que o que importa não é quanto se sabe de uma doença, mas a forma disso — "
    + "clara na genética, escura na história natural. Medida em cinco eixos, a previsão "
    + "falha: o conhecimento é MENOS concentrado do que a independência daria, e a estatística "
    + "acaba acompanhando quantos eixos estão preenchidos, não a forma deles.",
  ),
  shapeObserved: bi("observed anisotropy", "anisotropia observada"),
  shapeNull: bi("under independence", "sob independência"),
  shapeCorr: bi("Which axes move together", "Quais eixos andam juntos"),
  shapeCorrSub: bi(
    "The two strongest couplings are artefacts of how the axes were built, and they are "
    + "labelled as such. What survives is a registry boundary: HPO annotation is OMIM-heavy, "
    + "prevalence exists only under ORPHA codes, and every cross-catalogue pair is negative.",
    "Os dois acoplamentos mais fortes são artefatos de como os eixos foram construídos, e "
    + "estão marcados assim. O que sobra é um limite entre registros: a anotação do HPO é "
    + "pesada em OMIM, a prevalência só existe sob códigos ORPHA, e todo par entre catálogos "
    + "é negativo.",
  ),
  shapeArtefact: bi("artefact of construction", "artefato de construção"),
  shapeKept: bi(
    "Kept on the site rather than deleted. A catalogue of ideas where every idea works is a "
    + "catalogue nobody tested.",
    "Mantido no site em vez de apagado. Um catálogo de ideias onde toda ideia funciona é um "
    + "catálogo que ninguém testou.",
  ),

  // --------------------------------------------------------------- shared
  nullLabel: bi("null", "nulo"),
  ci: bi("95 % CI", "IC 95 %"),
  governed: bi(
    "Governed by ADR 0007: an idea has no standing here until a tool computes it from "
    + "ingested public data and writes a number with a null and an interval.",
    "Governado pelo ADR 0007: uma ideia não vale nada aqui até que uma ferramenta a compute "
    + "a partir de dado público ingerido e escreva um número com nulo e intervalo.",
  ),
} as const;
