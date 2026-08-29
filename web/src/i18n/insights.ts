/** The cross-layer observations, in both languages.
 *
 *  The RULES themselves are not here: they are written by tools/gene_insights.py and shipped
 *  with the data, because a rule is a measurement's own definition and a second copy in a
 *  translation file is a second chance for the two to disagree. Only the page's own words
 *  are translated. That is the same reason disease names and gene symbols are not translated
 *  anywhere on this site.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const INS = {
  section: bi("What two layers say together", "O que duas camadas dizem juntas"),
  group: bi("Observations", "Observações"),
  question: bi(
    "The findings that live in a disagreement between measurements, not inside any one of them.",
    "Os achados que moram numa discordância entre medições, não dentro de nenhuma delas.",
  ),

  lede: bi(
    "The panels before this show seven layers side by side and say nothing about what they "
    + "mean together. But almost everything worth knowing about a gene lives in a "
    + "disagreement between two measurements: a gene under strong selection in people that no "
    + "cell line needs, a gene every line needs that people break freely, a gene that clearly "
    + "matters and whose variants nobody can classify. Each observation below is a rule with "
    + "a stated threshold — never a score, never a ranking, never a composite.",
    "Os painéis anteriores mostram sete camadas lado a lado e não dizem nada sobre o que elas "
    + "significam juntas. Mas quase tudo que vale saber sobre um gene mora numa discordância "
    + "entre duas medições: um gene sob forte seleção em pessoas de que nenhuma linhagem "
    + "celular precisa, um gene de que toda linhagem precisa e que as pessoas quebram à "
    + "vontade, um gene que claramente importa e cujas variantes ninguém consegue "
    + "classificar. Cada observação abaixo é uma regra com limiar declarado — nunca um "
    + "escore, nunca um ranking, nunca um composto.",
  ),
  none: bi(
    "No rule fired for this gene. Every one below was applied and none matched — which is a "
    + "statement about the gene, not a gap in the page.",
    "Nenhuma regra disparou para este gene. Todas abaixo foram aplicadas e nenhuma casou — "
    + "o que é uma afirmação sobre o gene, não uma lacuna da página.",
  ),
  notFired: bi("Applied, and did not fire", "Aplicadas, e não dispararam"),
  ruleLabel: bi("Rule", "Regra"),
  ofEligible: bi("of the genes it could apply to", "dos genes a que ela podia se aplicar"),
} as const;
