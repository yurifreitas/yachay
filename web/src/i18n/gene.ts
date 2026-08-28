/** The gene navigator's words, in both languages.
 *
 *  This page is the one a clinician or a family is most likely to reach first — they arrive
 *  holding a symbol, not a method — so it is fully bilingual from the day it ships rather
 *  than translated later.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const GENE = {
  /* ------------------------------------------------------------------ groups */
  gScreen: bi("What the screen says", "O que a triagem diz"),
  qScreen: bi(
    "Whether cells need this gene, how strongly, and whether that is selective or merely toxic.",
    "Se as células precisam deste gene, com que força, e se isso é seletivo ou apenas tóxico.",
  ),
  gContext: bi("Where it sits", "Onde ele se situa"),
  qContext: bi(
    "Its position in the disease-gene graph: who it neighbours, and how much disease reaches it.",
    "A posição dele no grafo doença-gene: de quem é vizinho, e quanta doença chega até ele.",
  ),
  gClinic: bi("What it is linked to", "A que ele está ligado"),
  qClinic: bi(
    "Every catalogued disease, kept separate by the strength of the claim behind it.",
    "Toda doença catalogada, mantida separada pela força da afirmação por trás dela.",
  ),

  /* ---------------------------------------------------------------- sections */
  sDependency: bi("Dependency and calibration", "Dependência e calibração"),
  sCancer: bi("Cancers that need it", "Cânceres que precisam dele"),
  sGenotype: bi("Mutations that create the need", "Mutações que criam a necessidade"),
  sNetwork: bi("Position in the graph", "Posição no grafo"),
  sDisease: bi("Catalogued diseases", "Doenças catalogadas"),

  /* -------------------------------------------------------------------- hero */
  eyebrow: bi("One gene · every layer on this site",
              "Um gene · todas as camadas deste site"),
  title: bi(
    "Everything measured here about one gene, including what was measured and not found",
    "Tudo o que foi medido aqui sobre um gene, inclusive o que foi medido e não encontrado",
  ),
  lede: bi(
    "The rest of this site is organised by method: a screen here, an atlas there, a graph on "
    + "a third page. People do not arrive holding a method. They arrive holding a symbol — a "
    + "clinician with a variant report, a curator checking an annotation, a family that has "
    + "just been given a word. This inverts the index for them.",
    "O resto deste site é organizado por método: uma triagem aqui, um atlas ali, um grafo "
    + "numa terceira página. As pessoas não chegam com um método na mão. Chegam com um "
    + "símbolo — um clínico com um laudo de variante, um curador conferindo uma anotação, "
    + "uma família a quem acabaram de dar uma palavra. Isto inverte o índice para elas.",
  ),
  searchLabel: bi("Find a gene", "Procurar um gene"),
  searchPlaceholder: bi("symbol — NF2, CFTR, KRAS…", "símbolo — NF2, CFTR, KRAS…"),
  indexed: bi("genes indexed", "genes indexados"),
  pairs: bi("gene-disease pairs", "pares gene-doença"),
  loadFailed: bi(
    "The gene index has not been generated.",
    "O índice de genes não foi gerado.",
  ),

  /* ------------------------------------------------------------------- empty */
  emptyLede: bi(
    "Type a symbol above, or start with one of these — each is a different kind of answer.",
    "Digite um símbolo acima, ou comece por um destes — cada um é um tipo diferente de resposta.",
  ),
  seedNF2: bi(
    "a tumour suppressor with its own screen on this site",
    "um supressor tumoral com triagem própria neste site",
  ),
  seedCFTR: bi(
    "one gene, one disease, decades of evidence",
    "um gene, uma doença, décadas de evidência",
  ),
  seedSNRPD3: bi(
    "the screen's top score — and pan-essential, which is the warning",
    "o maior escore da triagem — e pan-essencial, que é o alerta",
  ),
  seedKRAS: bi(
    "needed by some cancers and not others",
    "necessário para alguns cânceres e não para outros",
  ),

  /* ------------------------------------------------------------------ layers */
  layer: {
    dependency: bi("Screen", "Triagem"),
    cancer: bi("Cancer subgroups", "Subgrupos de câncer"),
    genotype: bi("Genotype contrasts", "Contrastes por genótipo"),
    network: bi("Disease graph", "Grafo de doenças"),
    disease: bi("Catalogues", "Catálogos"),
  },

  /** What each layer says when it HAS something, and when it has been asked and has not.
   *  The two are separate sentences on purpose: "tested in 121 contrasts and selected in
   *  none" is a measurement, and "no data" is not. */
  layerHas: {
    dependency: bi("measured in {n} cell lines", "medido em {n} linhagens celulares"),
    cancer: bi("{n} of {scope} subgroups", "{n} de {scope} subgrupos"),
    genotype: bi("{n} of {scope} genotype contrasts", "{n} de {scope} contrastes por genótipo"),
    network: bi("{n} neighbours, {diseases} diseases", "{n} vizinhos, {diseases} doenças"),
    disease: bi("{n} catalogued diseases", "{n} doenças catalogadas"),
  },
  layerNone: {
    dependency: bi("not among the {scope} genes screened",
                   "não está entre os {scope} genes triados"),
    cancer: bi("tested against {scope} subgroups, selected in none",
               "testado contra {scope} subgrupos, selecionado em nenhum"),
    genotype: bi("tested against {scope} genotype contrasts, selected in none",
                 "testado contra {scope} contrastes por genótipo, selecionado em nenhum"),
    network: bi("absent from the {scope}-gene disease graph",
                "ausente do grafo de doenças com {scope} genes"),
    disease: bi("no catalogue links it to a phenotype",
                "nenhum catálogo o liga a um fenótipo"),
  },

  /* -------------------------------------------------------------- dependency */
  fScore: bi("Raw score", "Escore bruto"),
  fScoreSub: bi("top-20 mean over", "média do top-20 sobre"),
  fNull: bi("Null at this n", "Nulo neste n"),
  fNullSub: bi(
    "what pure noise reads at this many observations",
    "o que o ruído puro marca com esta quantidade de observações",
  ),
  fZ: bi("Calibrated z", "z calibrado"),
  fZSub: bi(
    "standard deviations above the null; 2.33 is the one-sided 99th percentile",
    "desvios-padrão acima do nulo; 2,33 é o percentil 99 unilateral",
  ),
  fRank: bi("Calibrated rank", "Posição calibrada"),
  fRankSub: bi("raw rank", "posição bruta"),
  fSelectivity: bi("Selectivity", "Seletividade"),
  fSelectivitySub: bi(
    "how concentrated the dependency is in few lines",
    "quão concentrada a dependência está em poucas linhagens",
  ),
  fMedian: bi("Median dependency", "Dependência mediana"),
  fMedianSub: bi(
    "how strong it is where it exists",
    "quão forte ela é onde existe",
  ),

  flagEssential: bi(
    "Flagged common-essential: nearly every cell line needs this gene. A high score here is "
    + "the metric measuring toxicity, not selectivity — a real dependency and a useless "
    + "target. This is the single most common way a screen misleads, and it is why the "
    + "shortlist removes these genes rather than ranking them.",
    "Marcado como essencial comum: praticamente toda linhagem celular precisa deste gene. "
    + "Um escore alto aqui é a métrica medindo toxicidade, não seletividade — uma "
    + "dependência real e um alvo inútil. Este é o modo mais comum de uma triagem enganar, "
    + "e é por isso que a lista curta remove estes genes em vez de ordená-los.",
  ),
  flagControl: bi(
    "This is a labelled non-essential control: a gene expected to do nothing. Its calibrated "
    + "z is a test of the null, not a finding about the gene.",
    "Este é um controle não-essencial rotulado: um gene do qual se espera nada. O z "
    + "calibrado dele é um teste do nulo, não um achado sobre o gene.",
  ),
  flagCandidate: bi(
    "Clears the noise floor and carries neither flag — this is what a candidate looks like "
    + "before anyone has validated anything.",
    "Passa do piso de ruído e não carrega nenhum dos marcadores — é assim que um candidato "
    + "se parece antes de qualquer validação.",
  ),

  aDependency: bi(
    "Not among the genes screened. The DepMap adapter measured",
    "Não está entre os genes triados. O adaptador DepMap mediu",
  ),

  /* ------------------------------------------------------------------ cancer */
  cancerLede: bi(
    "Subgroups whose cells need this gene more than every cell line outside the subgroup. "
    + "The effect size is the difference in mean dependency; q is the false-discovery rate "
    + "after correcting across every gene tested in that subgroup.",
    "Subgrupos cujas células precisam deste gene mais do que toda linhagem fora do subgrupo. "
    + "O tamanho de efeito é a diferença na dependência média; q é a taxa de falsas "
    + "descobertas após correção sobre todos os genes testados naquele subgrupo.",
  ),
  cSubgroup: bi("Subgroup", "Subgrupo"),
  cLevel: bi("Level", "Nível"),
  cEffect: bi("Effect", "Efeito"),
  cLines: bi("Lines", "Linhagens"),
  cTruncated: bi("Showing the strongest of", "Mostrando os mais fortes de"),
  aCancer: bi(
    "Tested against",
    "Testado contra",
  ),
  aCancerTail: bi(
    "cancer subgroups at three nesting levels, and selected in none. That is a measurement, "
    + "not a missing panel: this gene is needed no more by any one cancer than by the rest.",
    "subgrupos de câncer em três níveis de aninhamento, e selecionado em nenhum. Isso é uma "
    + "medição, não um painel faltando: este gene não é mais necessário a nenhum câncer em "
    + "particular do que aos demais.",
  ),

  /* ---------------------------------------------------------------- genotype */
  genotypeLede: bi(
    "Here the subgroup is not a catalogue label but a property of the cell: lines carrying a "
    + "damaging mutation in the named gene. That is the grouping a target programme acts on.",
    "Aqui o subgrupo não é um rótulo de catálogo, e sim uma propriedade da célula: linhagens "
    + "que carregam uma mutação deletéria no gene indicado. É este o agrupamento sobre o qual "
    + "um programa de alvos age.",
  ),
  gMutated: bi("Cells mutated in", "Células mutadas em"),
  aGenotype: bi("Tested against", "Testado contra"),
  aGenotypeTail: bi(
    "genotype-defined contrasts, and selected in none.",
    "contrastes definidos por genótipo, e selecionado em nenhum.",
  ),

  /* ----------------------------------------------------------------- network */
  networkLede: bi(
    "The graph is built from genes that share a disease. Position in it is not evidence "
    + "about the gene — it is evidence about how much attention the catalogue has paid to it.",
    "O grafo é construído a partir de genes que compartilham uma doença. A posição nele não é "
    + "evidência sobre o gene — é evidência sobre quanta atenção o catálogo deu a ele.",
  ),
  nDegree: bi("Neighbours", "Vizinhos"),
  nDegreeSub: bi("genes sharing at least one disease", "genes que compartilham ao menos uma doença"),
  nDiseases: bi("Diseases reaching it", "Doenças que chegam a ele"),
  nDiseasesSub: bi("in the catalogue join", "na junção dos catálogos"),
  nCommunity: bi("Community", "Comunidade"),
  nCommunitySub: bi(
    "the cluster it was assigned by modularity",
    "o agrupamento a que foi atribuído por modularidade",
  ),
  aNetwork: bi(
    "Absent from the disease-gene graph, which holds",
    "Ausente do grafo doença-gene, que contém",
  ),

  /* ----------------------------------------------------------------- disease */
  diseaseLede: bi(
    "Grouped by the strength of the claim, never merged. MENDELIAN says a variant in this "
    + "gene causes the disease; POLYGENIC says it contributes; UNKNOWN — the largest class in "
    + "the source — says the catalogue recorded a link and not what kind.",
    "Agrupadas pela força da afirmação, nunca fundidas. MENDELIAN diz que uma variante neste "
    + "gene causa a doença; POLYGENIC diz que contribui; UNKNOWN — a maior classe na fonte — "
    + "diz que o catálogo registrou uma ligação e não de que tipo.",
  ),
  dTruncated: bi("Showing the first of", "Mostrando as primeiras de"),
  aDisease: bi(
    "No catalogued disease links this gene to a phenotype. In a corpus where a third of the "
    + "diseases have no gene at all, that is as likely to be a statement about curation "
    + "effort as about biology.",
    "Nenhuma doença catalogada liga este gene a um fenótipo. Num corpus em que um terço das "
    + "doenças não tem gene nenhum, isso tem tanta chance de ser uma afirmação sobre esforço "
    + "de curadoria quanto sobre biologia.",
  ),
} as const;
