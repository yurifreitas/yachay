/** The predictive-technology layer, in both languages.
 *
 *  This area exists because a catalogue of clinical-AI cards typed from papers is exactly
 *  what ADR 0007 forbids. It starts from the one record that is published, dated and not
 *  self-reported — the regulator's own list — and everything it says is a count with a
 *  denominator rather than a claim about whether a model is good.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const DEV = {
  // ---------------------------------------------------------------- the family and view
  famTech: bi("Predictive technologies", "Tecnologias preditivas"),
  qFamTech: bi(
    "Not a leaderboard. What a regulator has actually permitted, and in which specialties.",
    "Não é um ranking. O que um regulador de fato permitiu, e em quais especialidades.",
  ),
  view: bi("Authorised devices", "Dispositivos autorizados"),
  viewBlurb: bi(
    "The FDA's own list of AI-enabled devices cleared for clinical use, counted.",
    "A lista da própria FDA de dispositivos com IA liberados para uso clínico, contada.",
  ),

  // ---------------------------------------------------------------- groups
  gWhat: bi("What is deployed", "O que está implantado"),
  qWhat: bi(
    "Authorisation is the one rung of a readiness scale that can be observed instead of claimed.",
    "Autorização é o único degrau de uma escala de prontidão que se observa em vez de afirmar.",
  ),
  gCheck: bi("Where the count misleads", "Onde a contagem engana"),
  qCheck: bi(
    "A review panel is not a disease area, and reading it as one made this tool wrong once.",
    "Um painel de revisão não é uma área de doença, e ler assim já deixou esta ferramenta errada.",
  ),

  // ---------------------------------------------------------------- sections
  sPanels: bi("Which specialties", "Quais especialidades"),
  panelHeading: bi(
    "one specialty holds three quarters of everything ever authorised",
    "uma especialidade detém três quartos de tudo que já foi autorizado",
  ),
  panelSub: bi(
    "1,524 AI-enabled devices authorised for clinical use in the United States since 1995, "
    + "by the FDA panel that reviewed them. This says nothing about accuracy or benefit — a "
    + "device here has been permitted, not shown to help anyone.",
    "1.524 dispositivos com IA autorizados para uso clínico nos Estados Unidos desde 1995, "
    + "pelo painel da FDA que os revisou. Isto nada diz sobre acurácia ou benefício — um "
    + "dispositivo aqui foi permitido, não demonstrado como útil a alguém.",
  ),
  sYears: bi("When it happened", "Quando aconteceu"),
  yearHeading: bi(
    "the curve is recent and steep",
    "a curva é recente e íngreme",
  ),
  yearSub: bi(
    "Authorisations by year of final decision. A field that reads as decades old in the "
    + "literature has almost all of its regulated surface built after 2019.",
    "Autorizações por ano da decisão final. Uma área que na literatura parece ter décadas "
    + "tem quase toda a sua superfície regulada construída depois de 2019.",
  ),
  sExpected: bi("What was expected, and what is there", "O esperado, e o que há"),
  expHeading: bi(
    "the specialties written down before the counts were read",
    "as especialidades escritas antes de as contagens serem lidas",
  ),
  expSub: bi(
    "A list of the fields a reader of this literature would expect, registered in the tool "
    + "before it counted anything — so an absence is a prediction that failed rather than an "
    + "observation chosen after the fact.",
    "Uma lista das áreas que um leitor desta literatura esperaria, registrada na ferramenta "
    + "antes de ela contar qualquer coisa — então uma ausência é uma previsão que falhou, e "
    + "não uma observação escolhida depois.",
  ),
  sSkin: bi("The correction", "A correção"),
  skinHeading: bi(
    "no dermatology panel is not the same as no device",
    "não haver painel de dermatologia não é o mesmo que não haver dispositivo",
  ),
  skinSub: bi(
    "The first version of this tool concluded from the absent panel that no AI device for "
    + "skin cancer had been authorised. That is false. A panel is the committee that reviewed "
    + "a device, not the disease it addresses — and the tool's own stated limitation is what "
    + "caught the error.",
    "A primeira versão desta ferramenta concluiu, do painel ausente, que nenhum dispositivo "
    + "de IA para câncer de pele tinha sido autorizado. Isso é falso. Painel é o comitê que "
    + "revisou o dispositivo, não a doença que ele trata — e foi a limitação escrita pela "
    + "própria ferramenta que pegou o erro.",
  ),
  sWho: bi("Who builds them", "Quem os constrói"),
  whoHeading: bi("and the companies behind the list", "e as empresas por trás da lista"),
  whoSub: bi(
    "Authorisations by company. A concentrated list is a statement about who can afford a "
    + "regulatory pathway, which is a different question from who can build a model.",
    "Autorizações por empresa. Uma lista concentrada é uma afirmação sobre quem consegue "
    + "pagar um caminho regulatório, que é outra pergunta que a de quem consegue construir "
    + "um modelo.",
  ),

  // ---------------------------------------------------------------- shared
  readiness: bi("readiness, observed rather than claimed",
                "prontidão, observada em vez de afirmada"),
  notQuality: bi("what this is not", "o que isto não é"),
} as const;
