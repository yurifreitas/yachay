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

  // --------------------------------------------------------------- turing
  turing: bi("A prediction from 1952", "Uma previsão de 1952"),
  turingSub: bi(
    "Turing's morphogenesis says form comes from a field with a geometry and a time. A "
    + "Reactome pathway is an inventory of reactions, so it should lose more where the "
    + "abnormality is a structure that formed wrongly than where it is a process running "
    + "wrongly. Split the twenty organ systems that way and it does.",
    "A morfogênese de Turing diz que a forma vem de um campo com geometria e tempo. Uma via "
    + "do Reactome é um inventário de reações, então ela deveria perder mais onde a anomalia "
    + "é uma estrutura que se formou errado do que onde é um processo rodando errado. Divida "
    + "os vinte sistemas orgânicos assim e é o que acontece.",
  ),
  turingCaveat: bi(
    "⚠ The retentions were already visible when the classification was written. This is a "
    + "description with a p-value, not a pre-registered test, and it is labelled that way in "
    + "the artefact too.",
    "⚠ As retenções já estavam visíveis quando a classificação foi escrita. Isto é uma "
    + "descrição com p-valor, não um teste pré-registrado, e está marcado assim no artefato "
    + "também.",
  ),

  // --------------------------------------------------------------- association arm
  assoc: bi("Before the decomposition, the association",
            "Antes da decomposição, a associação"),
  assocSub: bi(
    "The aggregate file cannot separate a contradiction from two claims about two conditions, "
    + "but it can say whether conflict TRAVELS with carrying more conditions. Held inside "
    + "submitter strata, because review depth drives both sides. The association survives "
    + "every stratum — and the gradient is the finding: where evidence is thin, conflict looks "
    + "like disagreement; where it is thick, it looks like context.",
    "O arquivo agregado não separa uma contradição de duas afirmações sobre duas condições, "
    + "mas diz se o conflito ANDA JUNTO com carregar mais condições. Segurado dentro de faixas "
    + "de submissores, porque profundidade de revisão empurra os dois lados. A associação "
    + "sobrevive a toda faixa — e o gradiente é o achado: onde a evidência é fina, conflito "
    + "parece discordância; onde é grossa, parece contexto.",
  ),
  assocRR: bi("risk ratio, 4+ conditions against 1", "razão de risco, 4+ condições contra 1"),
  submitters: bi("submitters", "submissores"),
  conditions: bi("conditions", "condições"),

  // --------------------------------------------------------------- controls
  sortBy: bi("Sort by", "Ordenar por"),
  sortPathway: bi("pathway retention", "retenção da via"),
  sortCell: bi("cell-type retention", "retenção celular"),
  sortSize: bi("diseases", "doenças"),
  pickLanguage: bi("Coverage by organ system, for", "Cobertura por sistema orgânico, em"),
  examples: bi("Real cases, from the archive", "Casos reais, do arquivo"),
  examplesSub: bi(
    "Each of these is one variant classified consistently within every condition it was "
    + "submitted against — and recorded as conflicting only because the conditions were "
    + "pooled.",
    "Cada uma destas é uma variante classificada de forma consistente dentro de cada condição "
    + "contra a qual foi submetida — e registrada como conflitante só porque as condições "
    + "foram jogadas juntas.",
  ),
  axesDefs: bi("What each axis counts", "O que cada eixo conta"),
  dominant: bi("Which axis dominates", "Qual eixo domina"),

  // --------------------------------------------------------------- hyperdimensional views
  matrixTitle: bi("Fourteen languages, twenty-three organ systems.",
                  "Catorze idiomas, vinte e três sistemas orgânicos."),
  matrixRead: bi(
    "Each cell is the share of that system's annotation mass readable in that language. Rows "
    + "descend from complete to absent; columns are sorted by mean coverage. The holes line "
    + "up vertically — the systems one language drops are the systems the others drop too.",
    "Cada célula é a fração da massa de anotação daquele sistema legível naquele idioma. As "
    + "linhas descem de completo a ausente; as colunas são ordenadas pela cobertura média. Os "
    + "buracos se alinham na vertical — os sistemas que um idioma abandona são os que os "
    + "outros abandonam também.",
  ),
  slopeTitle: bi("What one alphabet loses, the other recovers.",
                 "O que um alfabeto perde, o outro recupera."),
  slopeHint: bi("lines that rise are systems the spatial alphabet recovers",
                "linhas que sobem são sistemas que o alfabeto espacial recupera"),
  pcpTitle: bi("Twelve thousand diseases on five axes of what is known.",
               "Doze mil doenças em cinco eixos do que se sabe."),
  pcpHint: bi("diseases, drawn as density rather than as lines — at this count a polyline plot is a filled rectangle",
              "doenças, desenhadas como densidade e não como linhas — nesta contagem um gráfico de polilinhas é um retângulo cheio"),
  gridTitle: bi("Conflict rises with context, and faster the more reviewers there are.",
                "O conflito sobe com o contexto, e mais rápido quanto mais revisores há."),

  voidTitle: bi("What is not there, drawn as an object.",
                "O que não está lá, desenhado como objeto."),
  voidRead: bi(
    "Five axes cut into four bands each is a lattice of 1,024 ways a disease could be known. "
    + "Only 318 of them hold a disease. The rest are not background — a filled square is where "
    + "diseases sit, a ring is an ANTI-FORM: an empty region where the catalogue's own "
    + "marginals predict diseases and none are found. Ten pairwise faces, because five "
    + "dimensions cannot be drawn and a projection that hides which pair you are looking at is "
    + "worse than ten that say so.",
    "Cinco eixos cortados em quatro faixas cada é uma malha de 1.024 maneiras de uma doença ser "
    + "conhecida. Só 318 delas contêm alguma doença. O resto não é fundo — um quadrado cheio é "
    + "onde há doenças, um anel é uma ANTIFORMA: uma região vazia onde as próprias marginais do "
    + "catálogo preveem doenças e nenhuma é encontrada. Dez faces aos pares, porque cinco "
    + "dimensões não se desenham e uma projeção que esconde qual par você está vendo é pior que "
    + "dez que dizem.",
  ),
  voidFilled: bi("diseases sit here", "há doenças aqui"),
  voidAnti: bi("anti-form: expected and absent", "antiforma: esperada e ausente"),
  voidTop: bi("the largest absences, in diseases the marginals expected",
              "as maiores ausências, em doenças que as marginais esperavam"),

  // --------------------------------------------------------------- provenance
  prov: bi("Provenance, and what this does not say",
           "Proveniência, e o que isto não diz"),
  provRead: bi("Read from", "Lido de"),
  provMethod: bi("How it was computed", "Como foi computado"),
  provSays: bi("What it says", "O que diz"),
  provLimits: bi("Limits", "Limites"),
  provGenerated: bi("Generated", "Gerado em"),
  provOpen: bi("Show provenance", "Ver proveniência"),

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
