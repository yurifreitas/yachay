/** The command palette, in both languages. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const CMD = {
  label: bi("Find a gene", "Procurar um gene"),
  placeholder: bi("gene symbol — NF2, CFTR, KRAS…", "símbolo de gene — NF2, CFTR, KRAS…"),
  loading: bi("Loading the index…", "Carregando o índice…"),
  results: bi("matches", "resultados"),
  indexed: bi("genes indexed — start typing", "genes indexados — comece a digitar"),
  move: bi("move", "mover"),
  open: bi("open", "abrir"),
  close: bi("close", "fechar"),
  shortcut: bi("Ctrl-K to find a gene", "Ctrl-K para achar um gene"),
} as const;
