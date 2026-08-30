/** The site's own words, in both languages, side by side.
 *
 *  WHY ONE FILE AND NOT TWO. A `pt.ts` beside an `en.ts` is two files that drift: someone
 *  adds a section, updates one, and the other silently falls back for a year. Here the two
 *  languages are adjacent on the page — a missing translation is visible while writing it,
 *  and `Bi` makes it a type error rather than a fallback.
 *
 *  WHAT IS NOT HERE. Anything that comes from the data: gene symbols, run titles written by
 *  a manifest, disease names written by Orphanet. Those have one form. Translating a
 *  catalogue's own label would be inventing a record, which is the failure this whole
 *  repository is about.
 *
 *  ON THE PORTUGUESE. Statistical terms keep the form actually used in Brazilian scientific
 *  writing — "viés", "escore z", "razão de chances" — rather than a literal rendering. Where
 *  a term is genuinely untranslated in practice ("shortlist", "hexbin", "UpSet"), it stays,
 *  because a reader searching for it will search for that word.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

/* ------------------------------------------------------------------ the shell */

export const S = {
  /* quechua: to know. The tagline says what the name means, because a reader who does not
     recognise the word gets nothing from it otherwise. */
  tagline: bi("quechua: to know · free to use",
              "quechua: conhecer · livre para usar"),
  navLabel: bi("Sections of this site", "Seções deste site"),
  skip: bi("Skip to content", "Pular para o conteúdo"),
  loading: bi("Loading view", "Carregando a visão"),
  language: bi("Language", "Idioma"),
  findGene: bi("Find a gene", "Procurar um gene"),

  footer: bi(
    "Adapter-driven: every number and document comes from a manifest written by an analysis "
    + "run, converted by npm run data. A new adapter appears here without the UI knowing its "
    + "name, and nothing in this app is hand-typed.",
    "Movido a adaptadores: cada número e documento vem de um manifesto escrito por uma "
    + "execução de análise, convertido por npm run data. Um adaptador novo aparece aqui sem "
    + "que a interface saiba o nome dele, e nada neste site é digitado à mão.",
  ),

  /* Families of views, in the sidebar. */
  /* SIX FAMILIES WHERE THERE WERE FOUR, and every one of them now says what it answers.
     "Domains" held rare disease and cancer under one word — two different questions, two
     different literatures, and a reader holding one of them had to open the other to find
     out. The families name the reader's starting point, not the method's taxonomy. */
  /* THE FAMILIES NAME A QUESTION, NOT A CORPUS — and that took three attempts.
   *
   *  They were "Domains" holding rare disease and cancer together. Splitting those into two
   *  families was better and still wrong, because "rare disease" and "cancer" are not
   *  questions: they are enormous bodies of literature spanning different fields, and naming
   *  a family after one says nothing about what a reader will find inside.
   *
   *  What the site actually contains is four kinds of question. The one that matters most is
   *  the third: the cancer dependency screens, the DepMap runs and the obesity challenge are
   *  the SAME PROBLEM — a ranking built from unequally sampled observations by a selection
   *  operator — and filing them as three domains hid the only thing this repository claims
   *  they have in common. */
  famEntity: bi("Start from a gene", "Começar por um gene"),
  qFamEntity: bi(
    "You arrived holding a symbol. Everything this repository knows about one gene, in one place.",
    "Você chegou com um símbolo. Tudo o que este repositório sabe sobre um gene, num lugar só.",
  ),
  famEvidence: bi("Where the evidence stops", "Onde a evidência para"),
  qFamEvidence: bi(
    "The rare-disease catalogue as a map of its own gaps: what is known, at which scale, and "
    + "for whom.",
    "O catálogo de doenças raras como mapa das próprias lacunas: o que se sabe, em que escala, "
    + "e para quem.",
  ),
  famSelection: bi("Selection under unequal evidence", "Seleção sob evidência desigual"),
  qFamSelection: bi(
    "Cancer dependencies, CRISPR runs and the obesity screen are one problem: a ranking built "
    + "by a selection operator from observations that are not equally many.",
    "Dependências em câncer, execuções CRISPR e a triagem de obesidade são um problema só: um "
    + "ranking feito por um operador de seleção a partir de observações que não são igualmente "
    + "numerosas.",
  ),
  famMethod: bi("Method and proof", "Método e prova"),
  qFamMethod: bi(
    "The ten stages, the decision records, and what this repository got wrong on the way.",
    "Os dez estágios, os registros de decisão, e o que este repositório errou pelo caminho.",
  ),

  /* Views. */
  viewGene: bi("Gene navigator", "Navegador de genes"),
  viewGeneBlurb: bi(
    "Every layer on this site, for one gene — including what was measured and not found.",
    "Todas as camadas deste site, para um gene — inclusive o que foi medido e não encontrado.",
  ),
  viewCancer: bi("Cancer", "Câncer"),
  viewCancerBlurb: bi(
    "What each cancer needs that the others do not, by label and by genotype.",
    "O que cada câncer precisa e os outros não, por rótulo e por genótipo.",
  ),
  viewRare: bi("Rare disease", "Doença rara"),
  viewRareBlurb: bi(
    "An atlas of what is not known, where every gap is a typed value.",
    "Um atlas do que não se sabe, em que cada lacuna é um valor com tipo.",
  ),
  viewDocs: bi("Method", "Método"),
  viewDocsBlurb: bi(
    "The ten stages, every document in the repository, and what it rests on.",
    "Os dez estágios, todo documento do repositório, e sobre o que ele se apoia.",
  ),

  questionsIn: bi("Questions in", "Perguntas em"),
  panelsIn: bi("Panels in", "Painéis em"),
} as const;

/* ------------------------------------------------- the run dashboard (a screen) */

export const RUN = {
  gResult: bi("The shortlist", "A lista curta"),
  qResult: bi(
    "The deliverable, its inclusion rule, and what the two axes of selectivity say.",
    "O entregável, sua regra de inclusão, e o que dizem os dois eixos da seletividade.",
  ),
  gPremise: bi("Does the question hold?", "A pergunta se sustenta?"),
  qPremise: bi(
    "If observation counts do not vary, calibrating by n cannot change anything.",
    "Se a contagem de observações não varia, calibrar por n não muda nada.",
  ),
  gNull: bi("Is the null right?", "O nulo está certo?"),
  qNull: bi(
    "The floor every score is measured against, and the control that tests it.",
    "O piso contra o qual todo escore é medido, e o controle que o testa.",
  ),
  gEffect: bi("What calibration changes", "O que a calibração muda"),
  qEffect: bi(
    "Which entities move, how far, and whether the two rankings agree.",
    "Quais entidades se movem, quanto, e se os dois ordenamentos concordam.",
  ),
  gState: bi("Is this current?", "Isto está atual?"),
  qState: bi(
    "Which stage produced these numbers, and whether it is stale.",
    "Qual estágio produziu estes números, e se ele está desatualizado.",
  ),

  sShortlist: bi("The shortlist", "A lista curta"),
  sSelectivity: bi("The selectivity plane", "O plano da seletividade"),
  sPopulations: bi("Controls, essentials, candidates", "Controles, essenciais, candidatos"),
  sMultiplicity: bi("How many survive multiplicity", "Quantos sobrevivem à multiplicidade"),
  sTail: bi("How wrong the tail is", "O quanto a cauda está errada"),
  sCounts: bi("Count variation", "Variação da contagem"),
  sFloor: bi("The null floor", "O piso do nulo"),
  sRidge: bi("Null by observation count", "O nulo por contagem de observações"),
  sControl: bi("Control calibration", "Calibração dos controles"),
  sField: bi("The calibration field", "O campo de calibração"),
  sEvent: bi("The three populations", "As três populações"),
  sBump: bi("Where the raw top sixty went", "Para onde foram os sessenta primeiros"),
  sLineages: bi("One lineage, or all of them", "Uma linhagem, ou todas"),
  sShift: bi("Rank shift", "Deslocamento de posição"),
  sMovers: bi("Who moved", "Quem se moveu"),
  sOverlap: bi("Which flags overlap", "Quais marcadores se sobrepõem"),
  sBase: bi("What this rests on", "Sobre o que isto se apoia"),
  sProvenance: bi("Manifest", "Manifesto"),
} as const;

/* --------------------------------------------------------------------- cancer */

export const CANCER = {
  gCatalogue: bi("By catalogue label", "Por rótulo de catálogo"),
  qCatalogue: bi(
    "Oncotree lineage, disease and subtype — what each cancer needs that the others do not.",
    "Linhagem, doença e subtipo do Oncotree — o que cada câncer precisa e os outros não.",
  ),
  gGenotype: bi("By genotype", "Por genótipo"),
  qGenotype: bi(
    "What a damaging mutation makes a cell need, with lineage and burden measured rather "
    + "than disclaimed.",
    "O que uma mutação deletéria faz a célula precisar, com linhagem e carga mutacional "
    + "medidas em vez de ressalvadas.",
  ),

  sScale: bi("The contrast, and what it cancels", "O contraste, e o que ele cancela"),
  sPower: bi("What could be detected at all", "O que poderia ser detectado"),
  sSubgroup: bi("One subgroup, gated", "Um subgrupo, com as portas"),
  sShared: bi("Private or shared", "Privado ou compartilhado"),
  sControls: bi("Positive controls", "Controles positivos"),
  sGenotype: bi("Mutation as the grouping", "A mutação como agrupamento"),

  /* A SENTENCE PER PANEL, because the rail's label is a name and not a claim — the same gap
     the gene page had before ADR 0009, still open here because this page was never migrated
     and therefore never checked. Factual rather than interpretive: each names what the panel
     draws and which tool wrote the artefact behind it. */
  subScale: bi(
    "Effect size and its cancellation, from tools/cancer_subgroups.py at the level chosen "
    + "above. The contrast is a subgroup against every other line, so a dependency shared by "
    + "the whole panel cancels and does not appear.",
    "Tamanho de efeito e seu cancelamento, de tools/cancer_subgroups.py no nível escolhido "
    + "acima. O contraste é um subgrupo contra todas as outras linhagens, então uma "
    + "dependência comum ao painel inteiro se cancela e não aparece.",
  ),
  subPower: bi(
    "Every subgroup plotted by how many lines it has against the smallest effect that size "
    + "could detect. A subgroup below the curve produced no hits because it could not, which "
    + "is not the same as having none.",
    "Cada subgrupo plotado por quantas linhagens tem contra o menor efeito que esse tamanho "
    + "detectaria. Um subgrupo abaixo da curva não produziu achados porque não podia, o que "
    + "não é o mesmo que não ter nenhum.",
  ),
  subSubgroup: bi(
    "One subgroup's dependencies with the registered gates exposed. Moving a gate after "
    + "seeing the data is marked as re-gated, because a threshold chosen afterwards says "
    + "something about the threshold rather than about the biology.",
    "As dependências de um subgrupo com as portas registradas expostas. Mover uma porta "
    + "depois de ver o dado é marcado como re-gated, porque um limiar escolhido depois diz "
    + "algo sobre o limiar e não sobre a biologia.",
  ),
  subShared: bi(
    "Whether a dependency belongs to one subgroup or to many. A gene that is private to a "
    + "lineage is a different kind of claim from one that every panel needs.",
    "Se uma dependência pertence a um subgrupo ou a muitos. Um gene privado de uma linhagem "
    + "é uma afirmação de outra natureza que um gene de que todo painel precisa.",
  ),
  subControls: bi(
    "The dependencies named before the run as ones any working method must recover. A "
    + "shortlist whose positive controls fail is blocked rather than published.",
    "As dependências nomeadas antes da execução como as que qualquer método funcional tem "
    + "de recuperar. Uma lista cujos controles positivos falham é bloqueada, não publicada.",
  ),
  subGenotype: bi(
    "The same dependencies grouped by mutation instead of by lineage, drawn at all three "
    + "estimates from tools/cancer_genotype.py so the reader can see how much of each effect "
    + "survives stratification.",
    "As mesmas dependências agrupadas por mutação em vez de linhagem, desenhadas nas três "
    + "estimativas de tools/cancer_genotype.py para que se veja quanto de cada efeito "
    + "sobrevive à estratificação.",
  ),
} as const;

/* ---------------------------------------------------------------- rare disease */

export const RARE = {
  /* EIGHT SECTIONS UNDER ONE QUESTION IS A LIST, NOT A MAP.
     "What is known" held the catalogue, its denominators, its naming, and the diseases that
     fall outside every register — four different questions wearing one label. Split at the
     seam that was already there: what the catalogue COUNTS, and what it CALLS things. */
  /* THE FOUR BANDS. Each names a KIND of question rather than a subject, because the groups
     inside them already name subjects and repeating that one level up would be a second
     table of contents. */
  /* Bands for the gene page. The same idea as the atlas's: a run of groups that answer one
     KIND of question, so a reader can skip a band without reading the groups inside it. */
  tGene: bi("This gene", "Este gene"),
  tExperiment: bi("What experiments say", "O que os experimentos dizem"),
  tOnward: bi("Onward", "Adiante"),
  /* And for a run. A screen answers four questions in order and they were four peer groups. */
  tRun: bi("The run", "A execução"),
  tNull: bi("The null", "O nulo"),
  tEffect: bi("The effect", "O efeito"),
  tResult: bi("The result", "O resultado"),

  tCatalogue: bi("The catalogue", "O catálogo"),
  tLadder: bi("Where in the organism", "Onde no organismo"),
  tEstablished: bi("How well it is established", "Quão bem está estabelecido"),
  tArgument: bi("The argument", "O argumento"),

  gKnown: bi("The catalogue", "O catálogo"),
  qKnown: bi(
    "The whole catalogue first, because every later claim inherits its shape.",
    "O catálogo inteiro primeiro, porque toda afirmação seguinte herda a forma dele.",
  ),
  gNaming: bi("Names and gaps", "Nomes e lacunas"),
  qNaming: bi(
    "What a disease is called, what has no name yet, and who is missing from the register.",
    "Como uma doença é chamada, o que ainda não tem nome, e quem falta no registro.",
  ),
  gCause: bi("What it is of", "Do que ela é"),
  qCause: bi(
    "Gene, cell, network — and the diseases where the answer is not a gene at all.",
    "Gene, célula, rede — e as doenças em que a resposta não é um gene.",
  ),
  gCase: bi("One disease", "Uma doença"),
  qCase: bi(
    "A single record in full, and what a therapy for it would physically take.",
    "Um registro inteiro, e o que uma terapia para ele exigiria fisicamente.",
  ),
  gDecide: bi("How to decide", "Como decidir"),
  qDecide: bi(
    "What a case series can carry, and how to choose under your own constraints.",
    "O que uma série de casos sustenta, e como escolher sob as suas restrições.",
  ),
  gArgument: bi("The argument", "O argumento"),
  qArgument: bi(
    "The thesis this serves, its references, and where every figure came from.",
    "A tese que isto serve, suas referências, e de onde veio cada figura.",
  ),

  sWorld: bi("The whole catalogue", "O catálogo inteiro"),
  sBias: bi("What the data is really measuring", "O que o dado realmente mede"),
  sPopulation: bi("Whose numbers these are", "De quem são estes números"),
  sPatients: bi("What patients say", "O que os pacientes dizem"),
  sNames: bi("Names, history, taxonomy", "Nomes, história, taxonomia"),
  sAtlas: bi("Where the data stops", "Onde o dado termina"),
  sGaps: bi("Which gaps come together", "Quais lacunas andam juntas"),
  sCell: bi("Cell vs gene", "Célula x gene"),
  sNetwork: bi("The network, expandable", "A rede, expansível"),
  sSparse: bi("That graph, computationally", "Esse grafo, computacionalmente"),
  sNongene: bi("When it is not a gene", "Quando não é um gene"),
  sDisease: bi("By disease", "Por doença"),
  sCapability: bi("What it physically takes", "O que exige fisicamente"),
  sEvidence: bi("What the evidence supports", "O que a evidência sustenta"),
  sChoose: bi("Choose an approach", "Escolher uma abordagem"),
  sDims: bi("Ways of looking", "Modos de olhar"),
  sThesis: bi("The thesis under all of it", "A tese por trás de tudo"),
  sSelfAudit: bi("Does this agree with itself?", "Isto concorda consigo mesmo?"),
  sRefmap: bi("The reference map", "O mapa de referências"),
  sSources: bi("Sources and definitions", "Fontes e definições"),
} as const;

/* ---------------------------------------------------------------------- method */

export const DOCS = {
  gState: bi("The pipeline", "O pipeline"),
  qState: bi(
    "Which stages are current, what they read, and what they write.",
    "Quais estágios estão atuais, o que leem, e o que escrevem.",
  ),
  gRead: bi("The documents", "Os documentos"),
  qRead: bi(
    "Findings, decisions and method pages, rendered from the repository itself.",
    "Achados, decisões e páginas de método, renderizados do próprio repositório.",
  ),
  gTools: bi("The tooling", "O ferramental"),
  qTools: bi(
    "Which libraries and public resources this rests on, and which sit unused.",
    "Sobre quais bibliotecas e recursos públicos isto se apoia, e quais estão sem uso.",
  ),

  sStages: bi("Stage by stage", "Estágio por estágio"),
  sTools: bi("Libraries and resources", "Bibliotecas e recursos"),

  kMethod: bi("Method", "Método"),
  kFindings: bi("Findings", "Achados"),
  kCase: bi("Case studies", "Estudos de caso"),
  kAdr: bi("Decisions", "Decisões"),
} as const;
