/** Four measurements that existed only as JSON, in both languages.
 *
 *  Each of these was computed, verified and then rendered nowhere — the failure audit A29
 *  names, committed again on the newest work. The sentences below lead with what each
 *  measurement REFUSES to say, because that is the part a reader cannot recover from a
 *  number: a gap taxonomy that cannot tell "nobody looked" from "the biology forbids it",
 *  an attention arm with no severity coefficient at all, and a convergence with no z on
 *  any gene because the domain failed the adapter gate.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const MORE = {
  ci: bi("95 % interval", "intervalo 95 %"),
  unavailable: bi("not reported", "não reportado"),

  // ------------------------------------------------------------------ gaps
  sGaps: bi("What kind of hole is it", "Que tipo de buraco é"),
  gapHeading: bi(
    "gaps that close with a join, not a study",
    "lacunas que fecham com um join, não com um estudo",
  ),
  gapSub: bi(
    "Of 42,645 missing fields across 16,382 diseases, 16.1 % are cases where the OTHER "
    + "catalogue already has the fact and both halves are on this disk. That is not a "
    + "research gap. It is an unperformed join.",
    "De 42.645 campos ausentes em 16.382 doenças, 16,1 % são casos em que o OUTRO catálogo "
    + "já tem o fato e as duas metades estão neste disco. Isso não é lacuna de pesquisa. "
    + "É um join que ninguém fez.",
  ),
  gapFields: bi(
    "Read the interoperability column first: it is where a day of ingestion buys what a "
    + "study would take years to buy. Prevalence and onset carry 5,495 of the 6,874 between "
    + "them, and cell type carries none — nothing to join to, which is a different problem.",
    "Leia primeiro a coluna de interoperabilidade: é onde um dia de ingestão compra o que "
    + "um estudo levaria anos para comprar. Prevalência e idade de início carregam 5.495 "
    + "dos 6.874 juntas, e tipo celular carrega zero — não há a que juntar, o que é outro "
    + "problema.",
  ),

  // ------------------------------------------------------------------ attention
  sAtt: bi("Who gets studied", "Quem é estudado"),
  attHeading: bi(
    "attention tracks prevalence, and it still does after the confound is removed",
    "a atenção acompanha a prevalência, e continua acompanhando sem o confundidor",
  ),
  attSub: bi(
    "Rarer disorders are less studied. The obvious objection is that citations belong to the "
    + "GENE, not the disease — so the second arm drops every disease whose top gene clears "
    + "1,000 citations and the association survives at +0.254. The confound was measured "
    + "rather than disclaimed.",
    "Distúrbios mais raros são menos estudados. A objeção óbvia é que as citações pertencem "
    + "ao GENE, não à doença — então o segundo braço descarta toda doença cujo gene principal "
    + "passa de 1.000 citações e a associação sobrevive em +0,254. O confundidor foi medido, "
    + "não ressalvado.",
  ),
  attNeglected: bi(
    "the least-attended disorders in the arm",
    "os distúrbios com menos atenção no braço",
  ),

  // ------------------------------------------------------------------ autism
  sAut: bi("Where 714 disorders meet", "Onde 714 distúrbios se encontram"),
  autHeading: bi(
    "the convergence is spatial, not mechanistic",
    "a convergência é espacial, não mecanística",
  ),
  autSub: bi(
    "717 genes across 714 disorders carry an autism-related sign. They are LESS "
    + "pathway-concentrated than a size-matched random draw and MORE concentrated by the "
    + "cell type they are expressed in. A shared pathway is not a shared mechanism.",
    "717 genes em 714 distúrbios carregam um sinal relacionado a autismo. Eles são MENOS "
    + "concentrados por via do que um sorteio aleatório do mesmo tamanho e MAIS concentrados "
    + "pelo tipo celular onde se expressam. Via compartilhada não é mecanismo compartilhado.",
  ),
  autPrior: bi(
    "the prior was written down before the measurement ran",
    "a hipótese foi escrita antes de a medição rodar",
  ),
  autCommonest: bi("where they actually meet", "onde eles de fato se encontram"),

  // ------------------------------------------------------------------ void cells
  sVoid: bi("The combinations that are absent", "As combinações que faltam"),
  voidHeading: bi(
    "232 ways of knowing a disease that nobody occupies",
    "232 modos de conhecer uma doença que ninguém ocupa",
  ),
  voidSub: bi(
    "Each row is an empty cell of the five-axis lattice where the catalogue's own marginals "
    + "predict at least five diseases. It locates the absence; it does NOT say why — biology, "
    + "curation, or an axis that cannot be measured without the other four.",
    "Cada linha é uma célula vazia da grade de cinco eixos onde as marginais do próprio "
    + "catálogo preveem ao menos cinco doenças. Ela localiza a ausência; NÃO diz por quê — "
    + "biologia, curadoria, ou um eixo que não se mede sem os outros quatro.",
  ),
  voidAntiTable: bi("anti-forms, by how many diseases were expected",
                    "antiformas, por quantas doenças eram esperadas"),
  voidDensest: bi("and the cells that are crowded",
                  "e as células que estão lotadas"),
} as const;
