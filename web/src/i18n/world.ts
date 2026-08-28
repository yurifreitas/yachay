/** The world-knowledge panels, in both languages. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const WORLD = {
  /* ------------------------------------------------------------------ groups */
  gWorld: bi("What the world knows", "O que o mundo sabe"),
  qWorld: bi(
    "What the gene is, how badly it breaks, where it acts, and how unevenly any of that has "
    + "been established.",
    "O que o gene é, quão mal ele quebra, onde ele age, e quão desigualmente tudo isso foi "
    + "estabelecido.",
  ),

  /* ---------------------------------------------------------------- sections */
  sForm: bi("What it is", "O que ele é"),
  sConstraint: bi("How badly it breaks", "Quão mal ele quebra"),
  sExpression: bi("Where it acts", "Onde ele age"),
  sVariants: bi("Its variants, and who read them", "Suas variantes, e quem as leu"),

  /* -------------------------------------------------------------------- form */
  formLede: bi(
    "The functional annotation curators wrote for this protein. It is the sentence a reader "
    + "wants first, and it is the one thing on this page that no measurement in this "
    + "repository produces — sieve is about ranking under noise, not about function.",
    "A anotação funcional que curadores escreveram para esta proteína. É a frase que um "
    + "leitor quer primeiro, e é a única coisa nesta página que nenhuma medição deste "
    + "repositório produz — o sieve é sobre ordenar sob ruído, não sobre função.",
  ),
  formSize: bi("Length", "Comprimento"),
  formSizeSub: bi("amino-acid residues", "resíduos de aminoácidos"),
  aForm: bi(
    "No curated protein annotation for this symbol in the STRING release on disk.",
    "Sem anotação proteica curada para este símbolo na versão do STRING em disco.",
  ),

  /* -------------------------------------------------------------- constraint */
  constraintLede: bi(
    "How strongly human populations have selected against breaking this gene, measured across "
    + "gnomAD's exomes. LOEUF is the upper bound of observed-over-expected loss-of-function "
    + "variants; it is what gnomAD itself recommends ranking on, because it stays honest in "
    + "short genes where pLI becomes confident on almost no evidence.",
    "Com que força as populações humanas selecionaram contra a quebra deste gene, medido "
    + "sobre os exomas do gnomAD. LOEUF é o limite superior da razão observado/esperado de "
    + "variantes de perda de função; é a estatística que o próprio gnomAD recomenda para "
    + "ordenar, porque ela se mantém honesta em genes curtos, onde o pLI fica confiante com "
    + "quase nenhuma evidência.",
  ),
  cLoeuf: bi("LOEUF", "LOEUF"),
  cLoeufSub: bi(
    "upper bound of observed/expected LoF; under 0.35 is the constrained end",
    "limite superior de observado/esperado de perda de função; abaixo de 0,35 é a ponta restrita",
  ),
  cOe: bi("Observed / expected", "Observado / esperado"),
  cOeSub: bi("{obs} LoF variants seen, {exp} expected", "{obs} variantes de perda vistas, {exp} esperadas"),
  cPli: bi("pLI", "pLI"),
  cPliSub: bi(
    "the older statistic; kept because it is familiar, not because it is better",
    "a estatística mais antiga; mantida por ser familiar, não por ser melhor",
  ),
  cMisZ: bi("Missense z", "z de missense"),
  cMisZSub: bi(
    "the same idea for missense variation; above 3 is strong",
    "a mesma ideia para variação missense; acima de 3 é forte",
  ),
  bandConstrained: bi(
    "Constrained. Loss-of-function variants in this gene are strongly selected against in "
    + "human populations.",
    "Restrito. Variantes de perda de função neste gene sofrem forte seleção negativa nas "
    + "populações humanas.",
  ),
  bandMiddling: bi(
    "Middling. Some selection against loss of function, but not at the constrained end.",
    "Intermediário. Alguma seleção contra perda de função, mas não na ponta restrita.",
  ),
  bandTolerant: bi(
    "Tolerant. Loss-of-function variants occur about as often as chance would predict.",
    "Tolerante. Variantes de perda de função ocorrem com a frequência que o acaso preveria.",
  ),
  constraintCaution: bi(
    "Constraint is a population-genetic observation, not a claim about disease. It says that "
    + "breaking this gene was selected against over human history — evidence about "
    + "reproductive fitness, not evidence that this gene causes the condition in front of "
    + "you. Reading LOEUF as a pathogenicity score is the commonest misuse of gnomAD.",
    "Restrição é uma observação de genética de populações, não uma afirmação sobre doença. "
    + "Ela diz que quebrar este gene sofreu seleção negativa ao longo da história humana — "
    + "evidência sobre aptidão reprodutiva, não evidência de que este gene cause a condição "
    + "à sua frente. Ler LOEUF como escore de patogenicidade é o uso indevido mais comum do "
    + "gnomAD.",
  ),
  aConstraint: bi(
    "No gnomAD constraint for this gene. Usually the gene is too short for the bound to mean "
    + "anything, and gnomAD declining to state one is the honest outcome rather than a gap.",
    "Sem restrição do gnomAD para este gene. Em geral o gene é curto demais para que o "
    + "limite signifique algo, e o gnomAD não afirmar nada é o desfecho honesto, não uma "
    + "lacuna.",
  ),

  /* -------------------------------------------------------------- expression */
  expressionLede: bi(
    "Single-cell RNA across the Human Protein Atlas cell types. The breadth matters more than "
    + "the peak: a gene switched on in three cell types and one switched on in seventy-eight "
    + "are different problems, and a therapy aimed at the second has nowhere to hide.",
    "RNA de célula única nos tipos celulares do Human Protein Atlas. A amplitude importa mais "
    + "que o pico: um gene ligado em três tipos celulares e um ligado em setenta e oito são "
    + "problemas diferentes, e uma terapia dirigida ao segundo não tem onde se esconder.",
  ),
  eBreadth: bi("Cell types", "Tipos celulares"),
  eBreadthSub: bi(
    "of {total} carry it above {floor} nCPM",
    "de {total} o carregam acima de {floor} nCPM",
  ),
  ePeak: bi("Highest in", "Mais alto em"),
  eTable: bi("Cell type", "Tipo celular"),
  aExpression: bi(
    "No single-cell expression for this symbol in the Human Protein Atlas release on disk.",
    "Sem expressão de célula única para este símbolo na versão do Human Protein Atlas em disco.",
  ),

  /* ---------------------------------------------------------------- variants */
  variantsLede: bi(
    "Every variant submitted to ClinVar for this gene, by how it was classified.",
    "Toda variante submetida ao ClinVar para este gene, por como foi classificada.",
  ),
  vTotal: bi("Variants submitted", "Variantes submetidas"),
  vPathogenic: bi("Pathogenic", "Patogênicas"),
  vPathogenicSub: bi("including likely pathogenic", "incluindo provavelmente patogênicas"),
  vBenign: bi("Benign", "Benignas"),
  vBenignSub: bi("including likely benign", "incluindo provavelmente benignas"),
  vUncertain: bi("Uncertain significance", "Significado incerto"),
  vConflicting: bi("Conflicting", "Conflitantes"),
  vShare: bi("VUS share", "Fração de VUS"),

  /** The centrepiece of the panel, and the reason the layer exists. */
  vusHeadline: bi(
    "{pct} of this gene's submitted variants could not be classified",
    "{pct} das variantes submetidas deste gene não puderam ser classificadas",
  ),
  vusExplain: bi(
    "This is a measurement of attention, not a property of the gene. A variant of uncertain "
    + "significance is one nobody has had the cohort, the funding or the functional assay to "
    + "interpret — so the share tracks how much a gene has been studied, which tracks how "
    + "common its diseases are, which populations were sequenced, and which conditions got "
    + "societies and foundations behind them. A high share is the field saying it has not got "
    + "there yet, and it lands hardest on exactly the diseases with nobody to demand it.",
    "Isto é uma medição de atenção, não uma propriedade do gene. Uma variante de significado "
    + "incerto é uma que ninguém teve coorte, financiamento ou ensaio funcional para "
    + "interpretar — então a fração acompanha o quanto um gene foi estudado, o que acompanha "
    + "quão comuns são suas doenças, quais populações foram sequenciadas, e quais condições "
    + "tiveram sociedades e fundações por trás. Uma fração alta é a área dizendo que ainda "
    + "não chegou lá, e ela pesa mais exatamente sobre as doenças que não têm ninguém para "
    + "exigi-la.",
  ),
  vusTooFew: bi(
    "Only {n} variants have been submitted — too few for the uncertain share to mean anything. "
    + "The threshold used here is {min}, and it is stated so you can disagree with it.",
    "Apenas {n} variantes foram submetidas — poucas demais para que a fração de incertas "
    + "signifique algo. O limiar usado aqui é {min}, e ele é declarado para que você possa "
    + "discordar dele.",
  ),
  aVariants: bi(
    "No ClinVar submissions for this gene. In a corpus this large, that is a statement about "
    + "how much anyone has looked, not about the gene being quiet.",
    "Sem submissões ao ClinVar para este gene. Num corpus deste tamanho, isso é uma afirmação "
    + "sobre o quanto alguém olhou, não sobre o gene ser silencioso.",
  ),

  /* ------------------------------------------------------------------ layers */
  layerWorld: bi("World catalogues", "Catálogos mundiais"),
  layerWorldHas: bi("{n} of 4 public sources", "{n} de 4 fontes públicas"),
  layerWorldNone: bi(
    "absent from all four public sources",
    "ausente das quatro fontes públicas",
  ),
} as const;
