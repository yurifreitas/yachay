/** Who was in the sample, in both languages.
 *
 *  This group sits inside the rare atlas rather than in a pillar of its own, and the reason
 *  is the argument it makes: `gene_constraint` says in prose that gnomAD's panel is majority
 *  European, and this turns that sentence into a count on the disorders where the samples are
 *  largest. Separated into its own area it becomes another silo; next to the result it
 *  qualifies, it is an argument.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const SAMP = {
  // ---------------------------------------------------------------- the group
  group: bi("Who was sampled", "Quem foi amostrado"),
  question: bi(
    "On the findings human genetics is most confident about, whose genomes were read?",
    "Nos achados de que a genética humana mais tem certeza, de quem foram lidos os genomas?",
  ),

  // ---------------------------------------------------------------- ancestry
  sAncestry: bi("Ancestry of the samples", "Ancestralidade das amostras"),
  ancHeading: bi(
    "a caveat this site has been printing in prose, counted",
    "uma ressalva que este site vinha imprimindo em prosa, contada",
  ),
  ancSub: bi(
    "562 genome-wide analyses across nine psychiatric disorders, largely Psychiatric Genomics "
    + "Consortium output — the largest coordinated human-genetics effort on these conditions. "
    + "This is not a claim that any finding is wrong. It is a statement of the population "
    + "each one was established in.",
    "562 análises genômicas em nove transtornos psiquiátricos, em grande parte produção do "
    + "Psychiatric Genomics Consortium — o maior esforço coordenado de genética humana nessas "
    + "condições. Isto não afirma que algum achado esteja errado. Diz em que população cada "
    + "um foi estabelecido.",
  ),
  ancWeight: bi("composition, with each analysis counted once",
                "composição, com cada análise contando uma vez"),
  ancUnstated: bi("and the analyses that state no ancestry at all",
                  "e as análises que não declaram ancestralidade alguma"),

  // ---------------------------------------------------------------- per disorder
  sDisorders: bi("Disorder by disorder", "Transtorno a transtorno"),
  disHeading: bi(
    "four of the nine have no analysis with an African-ancestry majority",
    "quatro dos nove não têm nenhuma análise com maioria de ancestralidade africana",
  ),
  disSub: bi(
    "Not a small share — none. ADHD, OCD, anorexia nervosa and Tourette syndrome have zero "
    + "between them, and Tourette does not state the ancestry of half its sample weight.",
    "Não é uma fração pequena — é nenhuma. ADHD, TOC, anorexia nervosa e síndrome de Tourette "
    + "somam zero, e Tourette não declara a ancestralidade de metade do seu peso amostral.",
  ),
  disTable: bi("nine disorders, selected by MONDO term",
               "nove transtornos, selecionados por termo MONDO"),
  disCountries: bi("where the samples were recruited",
                   "onde as amostras foram recrutadas"),

  // ---------------------------------------------------------------- the comparison
  sAxes: bi("Every disease area, five axes", "Toda área de doença, cinco eixos"),
  pcpHeading: bi(
    "psychiatry is the least European of the eight areas, not the most",
    "psiquiatria é a MENOS europeia das oito áreas, não a mais",
  ),
  pcpSub: bi(
    "The previous panel says psychiatric samples are 65.8 % European, and read alone it "
    + "invites a conclusion about psychiatry. Against the other seven areas that conclusion "
    + "inverts: cancer is 80.8 % and the residual disease bucket 83.5 %. The problem is the "
    + "field's, and psychiatry is the part of it doing best.",
    "O painel anterior diz que as amostras psiquiátricas são 65,8 % europeias, e lido sozinho "
    + "convida a uma conclusão sobre psiquiatria. Contra as outras sete áreas essa conclusão "
    + "se inverte: câncer tem 80,8 % e a categoria residual de doenças, 83,5 %. O problema é "
    + "do campo, e a psiquiatria é a parte dele que vai melhor.",
  ),
  pcpAxes: bi("five axes, no two of them the same kind of quantity",
              "cinco eixos, nenhum par da mesma espécie de grandeza"),
  pcpAria: bi(
    "Parallel coordinates: one line per disease area across five axes",
    "Coordenadas paralelas: uma linha por área de doença em cinco eixos",
  ),
  pcpCategories: bi("where the categories came from", "de onde vieram as categorias"),

  sMatrix: bi("The composition grid", "A grade de composição"),
  matHeading: bi(
    "ancestry by disease area, ordered by the numbers rather than by the names",
    "ancestralidade por área de doença, ordenada pelos números e não pelos nomes",
  ),
  matSub: bi(
    "Both axes are seriated: rows and columns are placed so that similar profiles sit "
    + "together. Alphabetical order is also an argument — it argues that the names matter and "
    + "the numbers do not.",
    "Os dois eixos são seriados: linhas e colunas ficam de modo que perfis parecidos se "
    + "vizinhem. Ordem alfabética também é um argumento — ela argumenta que os nomes importam "
    + "e os números não.",
  ),
  matSeriated: bi("solved in Python, drawn in the browser",
                  "resolvido em Python, desenhado no navegador"),

  // ---------------------------------------------------------------- the joins
  sJoins: bi("How this was got wrong twice", "Como isto deu errado duas vezes"),
  joinHeading: bi(
    "one version returned 4.4 billion people, and another contradicted the field",
    "uma versão devolveu 4,4 bilhões de pessoas, e outra contradizia o campo",
  ),
  joinSub: bi(
    "Both errors are kept here at the size of the result, because the second was caught only "
    + "by being surprising — and an error of the same kind at a plausible magnitude would have "
    + "shipped.",
    "Os dois erros ficam aqui do tamanho do resultado, porque o segundo só foi pego por ser "
    + "surpreendente — e um erro da mesma natureza numa magnitude plausível teria sido "
    + "publicado.",
  ),
  joinUnit: bi("what is counted, and why it is not people",
               "o que é contado, e por que não são pessoas"),
} as const;
