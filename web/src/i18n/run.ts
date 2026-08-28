/** The run dashboard's own prose, in both languages.
 *
 *  Split out of `strings.ts` because that file holds the shell and the navigation — text
 *  every page shows — and this holds one page's argument. One file per page keeps a
 *  translator's working set to the page in front of them, and keeps the shell's dictionary
 *  small enough to read in one pass.
 *
 *  ON THE PORTUGUESE, again. This page argues about statistics, and the argument only
 *  survives translation if the terms are the ones used in Portuguese-language statistics:
 *  "estatística de ordem máxima", "taxa de falsas descobertas", "escore z calibrado". Where
 *  no settled term exists the English stays in italics in the prose rather than being
 *  invented here.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const RUNP = {
  /* ---------------------------------------------------------------- the shortlist */
  tShortlist: bi(
    "The deliverable, and the rule that produced it",
    "O entregável, e a regra que o produziu",
  ),
  sShortlist: bi(
    "Ranked by calibrated z with the common-essential genes removed, because a gene every "
    + "line needs is a real dependency and a useless selective one. The rule sits above the "
    + "table rather than in a footnote: a shortlist whose inclusion rule is invisible is an "
    + "opinion with a table around it.",
    "Ordenado pelo z calibrado, com os genes essenciais comuns removidos: um gene de que "
    + "toda linhagem precisa é uma dependência real e uma dependência seletiva inútil. A "
    + "regra fica acima da tabela e não em nota de rodapé — uma lista curta cuja regra de "
    + "inclusão é invisível é uma opinião com uma tabela em volta.",
  ),

  tOverlap: bi(
    "The flags are sets, and they overlap",
    "Os marcadores são conjuntos, e eles se sobrepõem",
  ),
  sOverlap: bi(
    "Everywhere else on this site a gene gets one class, because a legend wants three "
    + "colours. Here the flags are counted as the overlapping sets they actually are — "
    + "including the raw and calibrated top hundreds, whose intersection with "
    + "common-essential is the whole argument for calibrating, stated as a number.",
    "Em todo o resto deste site um gene recebe uma classe só, porque uma legenda quer três "
    + "cores. Aqui os marcadores são contados como os conjuntos sobrepostos que de fato são "
    + "— incluindo as cem primeiras posições bruta e calibrada, cuja interseção com "
    + "essencial comum é o argumento inteiro para calibrar, dito como número.",
  ),

  tSelectivity: bi(
    "The two axes that define the word selective",
    "Os dois eixos que definem a palavra seletivo",
  ),
  sSelectivity: bi(
    "How strong the dependency is where it exists, against how few lines carry it. Both "
    + "columns were already in the data and neither had ever been plotted.",
    "Quão forte é a dependência onde ela existe, contra em quão poucas linhagens ela "
    + "aparece. As duas colunas já estavam no dado e nenhuma havia sido plotada.",
  ),

  tPopulations: bi(
    "Three populations that should not look alike",
    "Três populações que não deveriam se parecer",
  ),
  sPopulations: bi(
    "Controls should sit at zero with unit spread; common essentials should sit far above "
    + "it; candidates should be somewhere a person has to think about. If the three collapse "
    + "together, the calibration has flattened the screen rather than corrected it.",
    "Os controles deveriam ficar em zero com dispersão unitária; os essenciais comuns, bem "
    + "acima; os candidatos, em algum lugar sobre o qual seja preciso pensar. Se os três "
    + "colapsam juntos, a calibração achatou a triagem em vez de corrigi-la.",
  ),

  tMultiplicity: bi(
    "Ranking 17,916 genes is itself a selection operator",
    "Ordenar 17.916 genes já é, em si, um operador de seleção",
  ),
  sMultiplicity: bi(
    "Calibrating each gene against a null of the right shape fixes half the problem. The "
    + "other half is that the top of seventeen thousand numbers is extreme for free. This "
    + "panel converts z to a p-value, tests the assumption that conversion rests on, and "
    + "reports what a false-discovery-rate cut actually buys over the threshold the shortlist "
    + "was using.",
    "Calibrar cada gene contra um nulo com a forma certa resolve metade do problema. A outra "
    + "metade é que o topo de dezessete mil números é extremo de graça. Este painel converte "
    + "o z em valor-p, testa a suposição sobre a qual essa conversão se apoia, e informa o "
    + "que um corte por taxa de falsas descobertas de fato compra sobre o limiar que a lista "
    + "curta vinha usando.",
  ),

  tTail: bi(
    "The normality test failed. This is by how much, and where",
    "O teste de normalidade falhou. Aqui está por quanto, e onde",
  ),
  sTail: bi(
    "A goodness-of-fit p-value says a distribution is wrong and nothing about where. At this "
    + "many observations almost anything fails a normality test, so the only question that "
    + "matters is whether the failure lives in the middle, where nobody looks, or in the "
    + "tail, where the entire shortlist lives.",
    "Um valor-p de aderência diz que a distribuição está errada e nada sobre onde. Com esta "
    + "quantidade de observações quase tudo reprova num teste de normalidade, então a única "
    + "pergunta que importa é se a falha mora no meio, onde ninguém olha, ou na cauda, onde "
    + "mora a lista curta inteira.",
  ),

  /* --------------------------------------------------------------- does it hold? */
  tCounts: bi(
    "If the counts do not vary, nothing downstream can",
    "Se as contagens não variam, nada rio abaixo pode variar",
  ),
  sCounts: bi(
    "Calibration divides by a null that depends on n. Where n is constant the correction is "
    + "a constant, and every ranking claim collapses to the raw one. This panel is first "
    + "because it can end the argument.",
    "A calibração divide por um nulo que depende de n. Onde n é constante a correção é uma "
    + "constante, e toda afirmação sobre ordenamento colapsa na bruta. Este painel vem "
    + "primeiro porque ele pode encerrar a discussão.",
  ),

  /* -------------------------------------------------------------- is the null right? */
  tFloor: bi(
    "The floor every score is measured against",
    "O piso contra o qual todo escore é medido",
  ),
  sFloor: bi(
    "A maximum over many observations rises with the number of observations even when "
    + "nothing is happening. The null says how much, at each n.",
    "Um máximo sobre muitas observações cresce com o número de observações mesmo quando nada "
    + "está acontecendo. O nulo diz quanto, para cada n.",
  ),

  tRidge: bi("The null, by observation count", "O nulo, por contagem de observações"),
  sRidge: bi(
    "One distribution per n. If these overlap, calibration is cosmetic; if they march, the "
    + "raw score was measuring the count.",
    "Uma distribuição por n. Se elas se sobrepõem, a calibração é cosmética; se elas "
    + "marcham, o escore bruto estava medindo a contagem.",
  ),

  tControl: bi(
    "The control, which is where this was caught being wrong",
    "O controle, que foi onde isto foi pego errado",
  ),
  sControl: bi(
    "Entities that should score at zero. A control that comes back at −4 is not a finding, "
    + "it is a broken null — and that is exactly what a pooled resample produced before the "
    + "null was drawn block-shaped.",
    "Entidades que deveriam pontuar zero. Um controle que volta em −4 não é um achado, é um "
    + "nulo quebrado — e foi exatamente isso que uma reamostragem agrupada produziu antes de "
    + "o nulo passar a ser sorteado em blocos.",
  ),

  /* ------------------------------------------------------------ what calibration does */
  tShift: bi("What the calibration moves", "O que a calibração move"),
  sShift: bi(
    "Raw rank against calibrated rank. A diagonal means the correction changed nothing; the "
    + "departures from it are the entire result.",
    "Posição bruta contra posição calibrada. Uma diagonal significa que a correção não mudou "
    + "nada; os desvios dela são o resultado inteiro.",
  ),

  tMovers: bi("Who moved, and by how much", "Quem se moveu, e por quanto"),
  sMovers: bi(
    "The table behind the shift, with both ranks and the distance between them.",
    "A tabela por trás do deslocamento, com as duas posições e a distância entre elas.",
  ),

  /* ------------------------------------------------------------------ is this current? */
  tBase: bi(
    "What every number on this page rests on",
    "Sobre o que cada número desta página se apoia",
  ),
  sBase: bi(
    "The dataset, the statistic and why its shape is the problem, the sampling model of the "
    + "null, the controls — and, at the end, what would show the whole thing is wrong.",
    "O conjunto de dados, a estatística e por que a forma dela é o problema, o modelo de "
    + "amostragem do nulo, os controles — e, no fim, o que mostraria que tudo isto está "
    + "errado.",
  ),

  tProvenance: bi("Where these numbers came from", "De onde vieram estes números"),
  sProvenance: bi(
    "The manifest the analysis wrote. Nothing on this page is typed by hand; a new adapter "
    + "appears here without the interface knowing its name.",
    "O manifesto que a análise escreveu. Nada nesta página é digitado à mão; um adaptador "
    + "novo aparece aqui sem que a interface saiba o nome dele.",
  ),

  /* ------------------------------------------------------- the hero's effect strip */
  eRho: bi("Rank agreement", "Concordância de ordenamento"),
  eRhoSub: bi(
    "Spearman between raw and calibrated order, over the {rows} rows in the bundle",
    "Spearman entre a ordem bruta e a calibrada, sobre as {rows} linhas do pacote",
  ),
  eMedian: bi("Median rank move", "Deslocamento mediano de posição"),
  eMedianSub: bi(
    "90th percentile {p90}, largest {max}",
    "percentil 90 {p90}, maior {max}",
  ),
  eOver100: bi("Moved more than 100 places", "Moveram-se mais de 100 posições"),
  eOver100Sub: bi("{pct}% of the shipped rows", "{pct}% das linhas enviadas"),
  eTop: bi("Top {n} shared", "Top {n} em comum"),
  eTopSub: bi(
    "entities present in both orderings — the shortlist the whole method exists to produce",
    "entidades presentes nos dois ordenamentos — a lista curta que o método inteiro existe "
    + "para produzir",
  ),
  eCounts: bi("Observation counts", "Contagens de observações"),
  eCountsSub: bi(
    "from {min} to {max}; without spread here, calibration by n can change nothing",
    "de {min} a {max}; sem dispersão aqui, calibrar por n não muda nada",
  ),
  eyebrow: bi("Screen · null-calibrated shortlist",
              "Triagem · lista curta calibrada pelo nulo"),
  labStatistic: bi("Statistic", "Estatística"),
  labReduction: bi("Reduction", "Redução"),
  caveat: bi(
    "The bundle ships {rows} of {total} entities — a density-preserving sample, not the head "
    + "and tail — so every figure in this strip is computed on that subset and says so. The "
    + "ranks inside the panels below are computed in Python over all {total}.",
    "O pacote traz {rows} de {total} entidades — uma amostra que preserva a densidade, não a "
    + "cabeça e a cauda — então cada número desta faixa é calculado sobre esse subconjunto e "
    + "diz isso. As posições dentro dos painéis abaixo são calculadas em Python sobre todas "
    + "as {total}.",
  ),
} as const;
