/** The gene datasheet, in both languages.
 *
 *  The vocabulary is deliberately the one an engineer reading a component datasheet already
 *  knows — parameter, symbol, min, typ, max, conditions — because the discipline being
 *  borrowed is theirs: no number without the circumstances that produced it.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const DS = {
  section: bi("Datasheet", "Datasheet"),
  group: bi("The gene as a component", "O gene como componente"),
  question: bi(
    "Every measurement with its minimum, its typical, its maximum and the conditions it was "
    + "obtained under.",
    "Cada medição com seu mínimo, seu típico, seu máximo e as condições em que foi obtida.",
  ),

  lede: bi(
    "A transistor datasheet does not print “gain: 100”. It prints a parameter, a symbol, a "
    + "minimum, a typical and a maximum, the unit, and the test conditions those were "
    + "obtained under — Vce = 5 V, Ic = 2 mA, Ta = 25 °C. Every number carries its "
    + "circumstances, and one without them is not publishable. Every other panel here reports "
    + "this gene's dependency as one number; it has 1,178 of them, and the spread is the "
    + "question a target programme is actually asking.",
    "Um datasheet de transistor não imprime “ganho: 100”. Imprime um parâmetro, um símbolo, "
    + "um mínimo, um típico e um máximo, a unidade, e as condições de teste em que foram "
    + "obtidos — Vce = 5 V, Ic = 2 mA, Ta = 25 °C. Cada número carrega suas circunstâncias, e "
    + "um sem elas não é publicável. Todo outro painel aqui reporta a dependência deste gene "
    + "como um número; ele tem 1.178, e a dispersão é a pergunta que um programa de alvos "
    + "está de fato fazendo.",
  ),
  convention: bi(
    "Where only one number was measured, the min and max columns are left empty. A datasheet "
    + "that repeats the typical across all three is claiming a range nobody measured — which "
    + "is the exact failure this repository exists to name.",
    "Onde só um número foi medido, as colunas de mínimo e máximo ficam vazias. Um datasheet "
    + "que repete o típico nas três está afirmando uma faixa que ninguém mediu — que é "
    + "exatamente a falha que este repositório existe para nomear.",
  ),

  hParam: bi("Parameter", "Parâmetro"),
  hSymbol: bi("Sym.", "Símb."),
  hMin: bi("Min", "Mín"),
  hTyp: bi("Typ", "Típ"),
  hMax: bi("Max", "Máx"),
  hUnit: bi("Unit", "Unid."),
  hCond: bi("Conditions", "Condições"),

  /* --------------------------------------------------------------- package */
  bPhysical: bi("Package", "Encapsulamento"),
  nPhysical: bi(
    "What the molecule physically is. The membrane passes are the pinout a cytosolic drug "
    + "cannot reach; the binding sites are where one can.",
    "O que a molécula fisicamente é. Os trechos transmembrana são a pinagem que um fármaco "
    + "citosólico não alcança; os sítios de ligação são onde ele alcança.",
  ),
  pLength: bi("Chain length", "Comprimento da cadeia"),
  pDomains: bi("Folded domains", "Domínios dobrados"),
  pMembrane: bi("Membrane passes", "Trechos transmembrana"),
  pBinding: bi("Binding sites", "Sítios de ligação"),
  pActive: bi("Catalytic residues", "Resíduos catalíticos"),
  uResidues: bi("aa", "aa"),
  cCurated: bi("UniProt, curated", "UniProt, curado"),

  /* ------------------------------------------------------- absolute maximum */
  bLimits: bi("Absolute maximum ratings", "Limites máximos absolutos"),
  nLimits: bi(
    "How much loss of function human populations tolerate. The o/e maximum is gnomAD's own "
    + "upper bound, not a point estimate — which is why it has a max column at all.",
    "Quanta perda de função as populações humanas toleram. O máximo de o/e é o limite "
    + "superior do próprio gnomAD, não uma estimativa pontual — por isso ele tem coluna de "
    + "máximo.",
  ),
  pOe: bi("LoF observed / expected", "Perda de função obs. / esp."),
  pPli: bi("LoF intolerance", "Intolerância a perda de função"),
  pMisZ: bi("Missense constraint", "Restrição a missense"),
  cObserved: bi("obs", "obs"),
  cExpected: bi("exp", "esp"),

  /* ------------------------------------------------------------ dependency */
  bDependency: bi("Dependency characteristics", "Características de dependência"),
  nDependency: bi(
    "CRISPR knockout across every screened cell line, read from the matrix rather than from "
    + "a summary. A gene needed at −1.8 in forty lines and 0.0 in the rest is a selective "
    + "target; −1.0 in every line is a poison. Both report a mean near −1.",
    "Nocaute CRISPR em cada linhagem celular triada, lido da matriz e não de um resumo. Um "
    + "gene necessário a −1,8 em quarenta linhagens e 0,0 no resto é um alvo seletivo; −1,0 "
    + "em todas é um veneno. Os dois reportam média perto de −1.",
  ),
  pEffect: bi("Gene effect", "Efeito do gene"),
  pIqr: bi("Interquartile range", "Intervalo interquartil"),
  pSpread: bi("Spread across lines", "Dispersão entre linhagens"),
  pDependent: bi("Lines that depend on it", "Linhagens que dependem dele"),
  pStrong: bi("Lines strongly dependent", "Linhagens fortemente dependentes"),
  uChronos: bi("Chronos", "Chronos"),
  cLines: bi("cell lines", "linhagens"),
  cQuartiles: bi("25th / 50th / 75th percentile", "percentis 25 / 50 / 75"),

  /* ------------------------------------------------------------ expression */
  bExpression: bi("Operating conditions", "Condições de operação"),
  nExpression: bi(
    "Where the gene is switched on. The minimum matters as much as the maximum: it is what a "
    + "therapy has to tolerate in every tissue that is not the target.",
    "Onde o gene está ligado. O mínimo importa tanto quanto o máximo: é o que uma terapia "
    + "tem de tolerar em cada tecido que não é o alvo.",
  ),
  pExpression: bi("Expression", "Expressão"),
  pFocus: bi("Focus", "Foco"),
  cCellTypes: bi("cell types", "tipos celulares"),
  cFocus: bi(
    "peak over typical — high means concentrated",
    "pico sobre típico — alto significa concentrado",
  ),

  /* -------------------------------------------------------------- variants */
  bVariants: bi("Quality and reliability", "Qualidade e confiabilidade"),
  nVariants: bi(
    "How much of the variant record can actually be used. The uncertain share is a "
    + "measurement of attention, not of the gene.",
    "Quanto do registro de variantes é de fato utilizável. A fração de incertas é uma medição "
    + "de atenção, não do gene.",
  ),
  pSubmitted: bi("Variants submitted", "Variantes submetidas"),
  pPathogenic: bi("Classified pathogenic", "Classificadas patogênicas"),
  pVus: bi("Uncertain significance", "Significado incerto"),
  cIncludingLikely: bi("including likely", "incluindo prováveis"),
  cVus: bi("share of all submitted", "fração de todas as submetidas"),

  absent: bi(
    "No parameter has been measured for this gene in any of the sources on disk.",
    "Nenhum parâmetro foi medido para este gene em nenhuma das fontes em disco.",
  ),
} as const;
