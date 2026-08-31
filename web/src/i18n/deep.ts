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
  sZAudit: bi("What is a z worth here?", "Quanto vale um z aqui?"),
  sCluster: bi("Are the groups real?", "Os grupos são reais?"),
  sEmbed: bi("What is a UMAP worth?", "Quanto vale um UMAP?"),
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
  csHeading: bi(
    "mean agreement between two runs of the same clustering, over twelve seeds",
    "concordância média entre duas execuções do mesmo agrupamento, em doze sementes",
  ),
  csMatrix: bi(
    "38,746 edges, drawn once each — and the ordering you can switch to check them",
    "38.746 arestas, cada uma desenhada uma vez — e a ordenação que dá para trocar e conferir",
  ),
  emHeading: bi(
    "of each gene's fifteen nearest neighbours on the page, that share were neighbours in the data",
    "dos quinze vizinhos mais próximos de cada gene na figura, essa fração era vizinha nos dados",
  ),
  emPair: bi(
    "the same data, the same algorithm, two random seeds",
    "os mesmos dados, o mesmo algoritmo, duas sementes aleatórias",
  ),
  emNumbers: bi(
    "reproducible and correct are not the same thing, and this figure is one of them",
    "reprodutível e correto não são a mesma coisa, e esta figura é só uma das duas",
  ),
  emPrior: bi(
    "and the question every clustering figure answers by assumption: is there anything there?",
    "e a pergunta que toda figura de agrupamento responde por suposição: existe algo ali?",
  ),
  emClusters: bi(
    "where the tidiness came from",
    "de onde veio a arrumação",
  ),
  csFlow: bi(
    "half the genes land somewhere else — this is where they go",
    "metade dos genes vai parar em outro lugar — é para cá que eles vão",
  ),
  csAgreement: bi(
    "is the grouping in the graph, or in the objective function?",
    "o agrupamento está no grafo ou na função objetivo?",
  ),
  csResolution: bi(
    "the score is flat across a range that changes the answer fourfold",
    "o escore é plano numa faixa que muda a resposta em quatro vezes",
  ),
  csConsensus: bi(
    "and how firmly each gene belongs to the group it was given",
    "e com que firmeza cada gene pertence ao grupo que recebeu",
  ),
  zaHeading: bi(
    "published z values on this site, and what a permutation null can actually support",
    "valores de z publicados neste site, e o que um nulo de permutação de fato sustenta",
  ),
  zaFigure: bi(
    "the loudest z of each artefact, with the error it inherits from its own denominator",
    "o maior z de cada artefato, com o erro herdado do próprio denominador",
  ),
  zaTight: bi(
    "the other failure, which is not about tails: a null with almost no spread",
    "a outra falha, que não é sobre caudas: um nulo quase sem dispersão",
  ),
  zaTightSays: bi(
    "knowledge_void reports 318 occupied lattice cells against a null of 575 with a standard "
    + "deviation of 0.95 — under one unit, on a count — and a z of -270.51. The shortfall is "
    + "real and it is one of the strongest measurements here. The z is not a measurement of "
    + "it: it is a statement about the size of a denominator. Where the null is this tight, "
    + "the effect on its own scale is the number that means something, and it is published "
    + "beside every one of these.",
    "knowledge_void reporta 318 células ocupadas contra um nulo de 575 com desvio padrão de "
    + "0,95 — menos de uma unidade, numa contagem — e um z de -270,51. O déficit é real e é "
    + "uma das medidas mais fortes daqui. O z não é a medida dele: é uma afirmação sobre o "
    + "tamanho de um denominador. Onde o nulo é assim tão apertado, o efeito na própria "
    + "escala é o número que significa algo, e ele é publicado ao lado de cada um destes.",
  ),
  conNulls: bi(
    "the four nulls themselves, with each measured value marked inside its own",
    "os quatro nulos em si, com cada valor medido marcado dentro do seu",
  ),
  hivUncK: bi(
    "and which of these would survive sequencing a different set of isolates",
    "e quais destes sobreviveriam a sequenciar outro conjunto de isolados",
  ),
  twinByZ: bi("ordered by z", "ordenado por z"),
  twinByTail: bi("ordered by the tail the permutation can resolve",
                 "ordenado pela cauda que a permutação consegue resolver"),
  twinByLb: bi("ordered by the bottom of the interval",
               "ordenado pelo piso do intervalo"),
  twinAgreement: bi("of these genes appear in both orderings, of",
                    "destes genes aparecem nas duas ordenações, de"),
  twinUncK: bi(
    "and how much of that reach survives dropping one causal gene",
    "e quanto desse alcance sobrevive a remover um gene causal",
  ),
  twinNoInterval: bi(
    "This disorder has fewer than three causal genes in the graph, so no interval is drawn: "
    + "a leave-one-out over two points is a single replicate, and a width computed from it "
    + "would be invented rather than measured. Seven of the eleven disorders are in this "
    + "position, which is itself the finding — most of the propagation here rests on one gene.",
    "Este distúrbio tem menos de três genes causais no grafo, então nenhum intervalo é "
    + "desenhado: um leave-one-out sobre dois pontos é uma única réplica, e uma largura "
    + "calculada daí seria inventada, não medida. Sete dos onze distúrbios estão nessa "
    + "situação, o que já é o achado — a maior parte da propagação aqui repousa sobre um gene.",
  ),
  twinIsNot: bi("what this is not", "o que isto não é"),
  twinLadder: bi("the rung this moves, and the ones it does not",
                 "o degrau que isto move, e os que não"),

  // ---------------------------------------------------------------- single-cell coverage
  sCells: bi("Has anyone collected a cell?", "Alguém já coletou uma célula?"),
  cellHeading: bi(
    "four layers reason over a cell axis that, for 99.5 % of these diseases, is an inference",
    "quatro camadas raciocinam sobre um eixo celular que, para 99,5 % destas doenças, é inferência",
  ),
  cellSub: bi(
    "Scale, autism convergence, the gap taxonomy and the knowledge lattice all place a "
    + "disease on a cell type, and all of them read an atlas of NORMAL tissue. CZ CELLxGENE "
    + "indexes the single-cell datasets that actually exist: 77 of 14,831 catalogue diseases "
    + "can be reached from one.",
    "Escala, convergência autista, taxonomia de lacunas e a grade de conhecimento colocam "
    + "uma doença num tipo celular, e todas leem um atlas de tecido NORMAL. O CZ CELLxGENE "
    + "indexa os conjuntos de célula única que existem de fato: 77 de 14.831 doenças do "
    + "catálogo alcançam algum.",
  ),
  cellBest: bi("the diseases that do have cells", "as doenças que têm células"),
  cellTissue: bi("and the tissues the field actually samples",
                 "e os tecidos que a área de fato amostra"),

  // ---------------------------------------------------------------- constraint
  sConstraint: bi("Intolerance to loss", "Intolerância à perda"),
  conHeading: bi(
    "the confound the attention result could state and not answer",
    "o confundidor que o resultado de atenção sabia enunciar e não respondia",
  ),
  conSub: bi(
    "gnomAD measures, for every gene, how much less loss-of-function variation appears in "
    + "800,000 exomes than mutation rate predicts. It is a property of the gene, measured in "
    + "a population nobody asked about disease — the only axis here that cannot have been "
    + "produced by the curation it is used to audit.",
    "O gnomAD mede, para cada gene, quanta variação de perda de função aparece a menos em "
    + "800.000 exomas do que a taxa de mutação prevê. É uma propriedade do gene, medida numa "
    + "população a quem ninguém perguntou sobre doença — o único eixo aqui que não pode ter "
    + "sido produzido pela curadoria que ele audita.",
  ),
  conMatched: bi("every arm against a length-matched null",
                 "cada braço contra um nulo pareado por comprimento"),
  conLength: bi("how much of the shift was length alone",
                "quanto do deslocamento foi só comprimento"),
  conBands: bi("the bands, so the table can be checked",
               "as faixas, para a tabela poder ser conferida"),

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
