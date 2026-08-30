/** Discovery — the method turned on a screen this repository did not curate.
 *
 *  Every other area here measures somebody's catalogue. This one measures an experiment, and
 *  it is the first adapter with a DESIGNED control pool: a non-targeting guide, in the same
 *  harness, 2,242 cells deep. The strings below carry that distinction because it is the
 *  reason this area exists rather than a detail of it.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const DISC = {
  // ---------------------------------------------------------------- family and view
  famDiscovery: bi("Discovery", "Descoberta"),
  qFamDiscovery: bi(
    "The method on an experiment, with a control that was designed rather than assumed.",
    "O método sobre um experimento, com um controle desenhado em vez de suposto.",
  ),
  view: bi("Obesity screen", "Triagem de obesidade"),
  viewBlurb: bi(
    "Stage 1 on the challenge's own top-3 aggregate, calibrated per cell count.",
    "Estágio 1 sobre o agregado top-3 da própria competição, calibrado por contagem de células.",
  ),

  // ---------------------------------------------------------------- bands and groups
  tScreen: bi("What can be calibrated", "O que dá para calibrar"),
  tResult: bi("What the calibration does", "O que a calibração faz"),

  gGate: bi("The gate", "O portão"),
  qGate: bi(
    "An adapter that does not fit lends this library's authority to a ranking it cannot defend.",
    "Um adaptador que não encaixa empresta a autoridade desta biblioteca a um ranking que ela não sustenta.",
  ),
  gFloor: bi("The floor", "O piso"),
  qFloor: bi(
    "What the same statistic produces on cells perturbed with nothing, at each cell count.",
    "O que a mesma estatística produz em células perturbadas com nada, a cada contagem.",
  ),
  gRank: bi("The ranking", "O ranking"),
  qRank: bi(
    "The competition's ordering against the same ordering judged at each perturbation's own n.",
    "A ordenação da competição contra a mesma ordenação julgada no n de cada perturbação.",
  ),

  // ---------------------------------------------------------------- sections
  sFit: bi("Does it fit?", "Encaixa?"),
  fitHeading: bi(
    "four yeses, and the fourth is in the column name",
    "quatro sins, e o quarto está no nome da coluna",
  ),
  fitSub: bi(
    "The four-question fit test, answered in writing before any code ran. The aggregate is "
    + "`agg_top3_z` — the mean of the top three of twelve correlated signatures — which is a "
    + "top-k, not a mean, and the cell counts behind it vary by more than eightyfold.",
    "O teste das quatro perguntas, respondido por escrito antes de qualquer código rodar. O "
    + "agregado é `agg_top3_z` — a média dos três melhores de doze assinaturas correlacionadas "
    + "—, que é um top-k e não uma média, e as contagens de células por trás variam mais de "
    + "oitenta vezes.",
  ),

  sControl: bi("The control pool", "O conjunto de controle"),
  controlHeading: bi(
    "the first designed control this library has had",
    "o primeiro controle desenhado que esta biblioteca teve",
  ),
  controlSub: bi(
    "The adapter skill ranks three ways to calibrate, and every adapter here until now used "
    + "the second or the third — the HIV one says out loud that it used the weakest. This "
    + "screen carries a non-targeting guide measured in the same experiment, so the null is "
    + "resampled from cells that were perturbed with nothing.",
    "A skill de adaptadores ranqueia três formas de calibrar, e todo adaptador daqui até "
    + "agora usou a segunda ou a terceira — o de HIV diz em voz alta que usou a mais fraca. "
    + "Esta triagem traz um guia não-alvo medido no mesmo experimento, então o nulo é "
    + "reamostrado de células perturbadas com nada.",
  ),

  sFloor: bi("What zero is worth", "Quanto vale o zero"),
  floorHeading: bi(
    "the floor moves more than tenfold across the counts this screen contains",
    "o piso varia mais de dez vezes nas contagens que esta triagem contém",
  ),
  floorSub: bi(
    "The same top-3 rule applied to resampled control cells. At eight cells the floor is "
    + "0.239 and the 95th percentile 0.695 — so a perturbation with eight cells has to beat "
    + "0.695 to mean anything, while the actual top perturbation of the screen scores 0.548 "
    + "on 224 cells.",
    "A mesma regra top-3 aplicada a células de controle reamostradas. Com oito células o piso "
    + "é 0,239 e o percentil 95 é 0,695 — então uma perturbação com oito células precisa "
    + "passar de 0,695 para significar algo, enquanto a melhor perturbação real da triagem "
    + "marca 0,548 com 224 células.",
  ),

  sRerank: bi("What it moves", "O que ela move"),
  rerankHeading: bi(
    "sixteen of the raw top twenty survive, and four do not",
    "dezesseis dos vinte do topo bruto sobrevivem, e quatro não",
  ),
  rerankSub: bi(
    "The competition's ordering against the same ordering with each perturbation judged at "
    + "its own cell count. This aggregate turns out to be reasonably robust — a result worth "
    + "reporting in its own right, because the same calibration removed two thirds of the "
    + "claims from a statistic in this repository's own gene pages.",
    "A ordenação da competição contra a mesma ordenação com cada perturbação julgada na "
    + "própria contagem de células. Este agregado se revela razoavelmente robusto — resultado "
    + "que vale por si, porque a mesma calibração removeu dois terços das afirmações de uma "
    + "estatística nas páginas de gene deste próprio repositório.",
  ),
} as const;
