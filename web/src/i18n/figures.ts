/** The figure index — the one page whose job is being found from. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const FIG = {
  title: bi("Every figure, by form", "Todas as figuras, por forma"),
  sub: bi(
    "Forty-six sections labelled with questions are the right thing for reading and the wrong "
    + "thing for finding a picture. This index is generated from the source: a figure added "
    + "without touching this page appears here, and one deleted leaves.",
    "Quarenta e seis seções rotuladas com perguntas são a coisa certa para ler e a errada "
    + "para achar uma figura. Este índice é gerado a partir do código: uma figura adicionada "
    + "sem tocar nesta página aparece aqui, e uma removida sai.",
  ),
  indexed: bi("indexed", "indexadas"),
  forms: bi("forms", "formas"),
  cssNotIndexed: bi(
    "marks drawn in CSS and not indexed",
    "marcas desenhadas em CSS e não indexadas",
  ),
  searchPlaceholder: bi(
    "Search a form, a subject, a section…",
    "Busque uma forma, um assunto, uma seção…",
  ),
  byForm: bi("Filter by form", "Filtrar por forma"),
  allForms: bi("All", "Todas"),
  open: bi("open →", "abrir →"),
  unplaced: bi("section not resolved", "seção não resolvida"),
  noLabel: bi("no description on this figure", "sem descrição nesta figura"),
  none: bi("Nothing matches that.", "Nada corresponde a isso."),
} as const;
