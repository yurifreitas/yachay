/** The four routes the rare atlas became, named.
 *
 *  The atlas was one entry in the rail answering four different questions, so a reader who
 *  came for one scrolled past three. The bands over its groups were already the seam — each
 *  named the KIND of question a run of groups answers — so each band is a view now.
 *
 *  These labels are what the rail shows. They are questions, not subjects, for the same
 *  reason the families are: a name that says "rare disease" tells a reader nothing about
 *  which of forty panels they are about to meet.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const RARE_VIEW_LABEL: Record<string, { label: Bi; blurb: Bi }> = {
  catalogue: {
    label: bi("The catalogue", "O catálogo"),
    blurb: bi(
      "14,831 entries, what their counters are really measuring, and what has no name yet.",
      "14.831 entradas, o que os contadores realmente medem, e o que ainda não tem nome.",
    ),
  },
  ladder: {
    label: bi("Where in the organism", "Onde no organismo"),
    blurb: bi(
      "Cell, signalling and molecule — the rungs where a coarser description loses what it "
      + "knew.",
      "Célula, sinalização e molécula — os degraus onde uma descrição mais grossa perde o que "
      + "sabia.",
    ),
  },
  established: {
    label: bi("How well it is established", "Quão bem está estabelecido"),
    blurb: bi(
      "The shape of the known, who was in the sample, and what biases the register.",
      "A forma do conhecido, quem estava na amostra, e o que enviesa o registro.",
    ),
  },
  argument: {
    label: bi("The argument", "O argumento"),
    blurb: bi(
      "The thesis this serves, its references, its self-audit — and the method outside rare "
      + "disease.",
      "A tese que isto serve, suas referências, sua autoauditoria — e o método fora da doença "
      + "rara.",
    ),
  },
};
