/** The routes out of a gene, in both languages. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const REL = {
  section: bi("Where to go next", "Para onde ir daqui"),
  group: bi("Related genes", "Genes relacionados"),
  question: bi(
    "Four routes out of this gene, each one stating the relation that produced it.",
    "Quatro caminhos a partir deste gene, cada um declarando a relação que o produziu.",
  ),

  lede: bi(
    "A gene is never the unit of a real question. Each route below states WHY it is a route — "
    + "a related-genes list with no stated relation is guesswork with a layout, and it is the "
    + "commonest way an interface smuggles in a similarity score nobody can audit. There is "
    + "no embedding here and no composite: the order is shared evidence, and the count that "
    + "produced it is printed.",
    "Um gene nunca é a unidade de uma pergunta real. Cada caminho abaixo declara POR QUE é um "
    + "caminho — uma lista de genes relacionados sem relação declarada é chute com layout, e "
    + "é o jeito mais comum de uma interface contrabandear um escore de similaridade que "
    + "ninguém consegue auditar. Aqui não há embedding nem composto: a ordem é evidência "
    + "compartilhada, e a contagem que a produziu vai impressa.",
  ),

  rGraph: bi("Shares a disease", "Compartilha uma doença"),
  nGraph: bi(
    "From the disease-gene graph: these genes are implicated in at least one of the same "
    + "catalogued conditions. The badge is how many they share.",
    "Do grafo doença-gene: estes genes estão implicados em ao menos uma das mesmas condições "
    + "catalogadas. O selo é quantas eles compartilham.",
  ),
  rDisease: bi("Named by the same disease", "Nomeados pela mesma doença"),
  nDisease: bi(
    "The tightest disease this gene belongs to — a condition naming forty genes is a "
    + "syndrome, not a lead, so the smallest one is shown.",
    "A doença mais restrita a que este gene pertence — uma condição que nomeia quarenta genes "
    + "é uma síndrome, não uma pista, então a menor é mostrada.",
  ),
  rFamily: bi("Same fold", "Mesmo dobramento"),
  nFamily: bi(
    "Shares a UniProt domain family: the same fold doing the same job in a different protein. "
    + "The most specific family this gene belongs to, because a route out through a "
    + "476-member kinase family is barely a route.",
    "Compartilha uma família de domínio do UniProt: o mesmo dobramento fazendo o mesmo "
    + "trabalho em outra proteína. A família mais específica a que este gene pertence, porque "
    + "uma saída por uma família de quinase com 476 membros mal é uma saída.",
  ),
  rLineage: bi("Needed by the same cancer", "Necessário ao mesmo câncer"),
  nLineage: bi(
    "Selected in the same DepMap subgroup: an experiment said these cells need both. Shown "
    + "for the subgroup where this gene's effect is strongest.",
    "Selecionados no mesmo subgrupo do DepMap: um experimento disse que estas células "
    + "precisam dos dois. Mostrado para o subgrupo em que o efeito deste gene é mais forte.",
  ),

  showingOf: bi("showing {shown} of {total}", "mostrando {shown} de {total}"),
  geneCount: bi("{n} genes", "{n} genes"),
  sharedDiseases: bi("{n} shared diseases", "{n} doenças em comum"),
  absent: bi(
    "No route out: this gene shares no catalogued disease, no annotated fold family and no "
    + "cancer subgroup with any other gene in the index. In a corpus this size that is "
    + "usually a statement about how little has been recorded, not about isolation.",
    "Nenhuma saída: este gene não compartilha doença catalogada, família de dobramento "
    + "anotada nem subgrupo de câncer com nenhum outro gene do índice. Num corpus deste "
    + "tamanho isso costuma ser afirmação sobre o quão pouco foi registrado, não sobre "
    + "isolamento.",
  ),
} as const;
