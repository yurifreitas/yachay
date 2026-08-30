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
