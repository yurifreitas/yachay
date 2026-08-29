/** The attention panel, in both languages. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const ATT = {
  section: bi("How much anyone looked", "O quanto alguém olhou"),
  group: bi("Attention", "Atenção"),
  question: bi(
    "The bias every other panel invokes, measured instead of asserted.",
    "O viés que todo outro painel invoca, medido em vez de afirmado.",
  ),

  lede: bi(
    "Every panel on this site invokes attention bias — the VUS share “is a measurement of "
    + "attention, not of the gene”, constraint “is measured where people sequenced”, a "
    + "protein with no annotated domain “is usually one nobody has characterised”. All of it "
    + "was asserted and none of it was measured. NCBI's gene2pubmed is the measurement: one "
    + "row per gene per indexed paper.",
    "Todo painel deste site invoca viés de atenção — a fração de VUS “é uma medição de "
    + "atenção, não do gene”, restrição “é medida onde sequenciaram”, uma proteína sem "
    + "domínio anotado “em geral é uma que ninguém caracterizou”. Tudo isso era afirmado e "
    + "nada era medido. O gene2pubmed do NCBI é a medição: uma linha por gene por artigo "
    + "indexado.",
  ),

  pPapers: bi("Indexed papers", "Artigos indexados"),
  sPapers: bi("median across all genes {median}; most studied {max}",
              "mediana entre todos os genes {median}; mais estudado {max}"),
  pResidual: bi("Unreadable, above its decile", "Ilegível, acima do seu decil"),
  sResidualHigh: bi(
    "Harder to read than genes studied as much — the field looked and still cannot classify it",
    "Mais difícil de ler que genes estudados o mesmo tanto — olharam e ainda não classificam",
  ),
  sResidualLow: bi(
    "Easier to read than genes studied as much",
    "Mais fácil de ler que genes estudados o mesmo tanto",
  ),
  sResidualPar: bi(
    "About what a gene this studied usually shows",
    "Mais ou menos o que um gene tão estudado costuma mostrar",
  ),

  ladderTitle: bi(
    "The claim, as a gradient",
    "A afirmação, como gradiente",
  ),
  ladderNote: bi(
    "Genes in ten equal groups by how many papers cite them, and the median share of their "
    + "variants nobody could classify. It falls the whole way down. The site's central caveat "
    + "is not a caveat: it is a measured relationship, and this is the row your gene sits in.",
    "Genes em dez grupos iguais por quantos artigos os citam, e a mediana da fração de "
    + "variantes que ninguém conseguiu classificar. Ela cai do começo ao fim. A ressalva "
    + "central do site não é ressalva: é uma relação medida, e esta é a faixa em que seu gene "
    + "está.",
  ),

  spaceTitle: bi("The measurement space", "O espaço das medições"),
  spaceRead: bi(
    "Each line is one gene crossing five measurements; every axis is a RANK, not a value, so "
    + "the top of each is “most” of that thing. A rule catches genes that cross the space in "
    + "a particular shape — pick one and watch where its lines part from the crowd. If they "
    + "do not part, the rule is relabelling the middle.",
    "Cada linha é um gene atravessando cinco medições; todo eixo é uma POSIÇÃO relativa, não "
    + "um valor, então o topo de cada um é “mais” daquilo. Uma regra pega genes que "
    + "atravessam o espaço com uma forma — escolha uma e veja onde as linhas dela se separam "
    + "do bolo. Se não se separam, a regra está só re-rotulando o meio.",
  ),

  axPapers: bi("studied", "estudado"),
  axPapersTop: bi("most", "mais"),
  axPapersBottom: bi("least", "menos"),
  axConstraint: bi("constrained", "restrito"),
  axConstraintTop: bi("most", "mais"),
  axConstraintBottom: bi("tolerant", "tolerante"),
  axDependency: bi("cells need it", "células precisam"),
  axDependencyTop: bi("most lines", "quase todas"),
  axDependencyBottom: bi("no line", "nenhuma"),
  axBreadth: bi("expressed", "expresso"),
  axBreadthTop: bi("everywhere", "em toda parte"),
  axBreadthBottom: bi("narrow", "restrito"),
  axUnread: bi("unreadable", "ilegível"),
  axUnreadTop: bi("most VUS", "mais VUS"),
  axUnreadBottom: bi("least", "menos"),

  axisOrder: bi("Axis order", "Ordem dos eixos"),
  moveLeft: bi("move left", "mover para a esquerda"),
  moveRight: bi("move right", "mover para a direita"),
  linesDrawn: bi("{n} genes drawn", "{n} genes desenhados"),
  linesLit: bi("{n} highlighted", "{n} destacados"),
} as const;
