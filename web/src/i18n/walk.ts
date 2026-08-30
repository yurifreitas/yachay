/** The sequence control, in both languages.
 *
 *  It shipped with its chrome hardcoded in English on a site where every other label is a
 *  `Bi` pair — visible as "enters O argumento" on a Portuguese page, half a sentence in each
 *  language. The section labels it prints were already translated; only the words around
 *  them were not.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const WALK = {
  prev: bi("previous", "anterior"),
  next: bi("next", "próxima"),
  /** Named, not implied: this is the only step in the interface that changes the question. */
  enters: bi("enters", "entra em"),
  atStart: bi("start of the sequence", "início da sequência"),
  atEnd: bi("end of the sequence", "fim da sequência"),
  aria: bi("Move through the sections in order",
           "Percorrer as seções na ordem"),
} as const;
