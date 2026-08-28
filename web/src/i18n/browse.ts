/** The browse-by-facet surface, in both languages. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const BROWSE = {
  title: bi("Or come in by a property", "Ou entre por uma propriedade"),
  lede: bi(
    "A search box serves someone who already knows the symbol. A curator wants every kinase; "
    + "a therapy team wants the genes one cancer needs; a clinician wants the genes whose "
    + "reports come back uncertain. None of them can type their way there. Every class below "
    + "is a measurement already on this site — nothing here is a category someone invented.",
    "Uma caixa de busca serve a quem já sabe o símbolo. Um curador quer todas as quinases; "
    + "um time de terapia quer os genes de que um câncer precisa; um clínico quer os genes "
    + "cujos laudos voltam inconclusivos. Nenhum deles chega lá digitando. Cada classe abaixo "
    + "é uma medição que já está neste site — nada aqui é categoria que alguém inventou.",
  ),

  kind: {
    domain: bi("Molecular part", "Parte molecular"),
    lineage: bi("Cancer that needs it", "Câncer que precisa dele"),
    constraint: bi("How badly it breaks", "Quão mal ele quebra"),
    interpretation: bi("Can its variants be read", "Dá para ler suas variantes"),
    breadth: bi("Where it acts", "Onde ele age"),
    route: bi("How it breaks", "Como ele quebra"),
  },

  note: {
    domain: bi(
      "UniProt domain families, with the trailing ordinals stripped so “Protein kinase 1” "
      + "and “Protein kinase 2” are one family. Crude on purpose: a real domain ontology is "
      + "InterPro, and it is not on disk.",
      "Famílias de domínio do UniProt, com os ordinais finais removidos para que "
      + "“Protein kinase 1” e “Protein kinase 2” sejam uma família. Grosseiro de "
      + "propósito: uma ontologia de domínio de verdade é o InterPro, e ele não está em disco.",
    ),
    lineage: bi(
      "Cancer lineages from the DepMap contrast: the genes this lineage needs more than every "
      + "cell line outside it, after correcting across every gene tested.",
      "Linhagens de câncer do contraste DepMap: os genes de que esta linhagem precisa mais "
      + "do que toda linhagem fora dela, após correção sobre todos os genes testados.",
    ),
    constraint: bi(
      "gnomAD LOEUF bands. The constrained end is where a new disease gene is most likely to "
      + "be hiding — and constraint is population genetics, not a claim about disease.",
      "Faixas de LOEUF do gnomAD. A ponta restrita é onde um novo gene de doença tem mais "
      + "chance de estar escondido — e restrição é genética de populações, não afirmação "
      + "sobre doença.",
    ),
    interpretation: bi(
      "The ClinVar uncertain share, banded, over genes with at least twenty submitted "
      + "variants. The top band is the working definition of a gene the clinic cannot use "
      + "yet — and it is a measurement of attention, not of the gene.",
      "A fração de incertas do ClinVar, em faixas, sobre genes com ao menos vinte variantes "
      + "submetidas. A faixa de cima é a definição prática de um gene que a clínica ainda "
      + "não consegue usar — e é uma medição de atenção, não do gene.",
    ),
    breadth: bi(
      "How many Human Protein Atlas cell types express it above the stated floor. A gene in "
      + "three is a different target from a gene in seventy-eight.",
      "Quantos tipos celulares do Human Protein Atlas o expressam acima do piso declarado. Um "
      + "gene em três é um alvo diferente de um gene em setenta e oito.",
    ),
    route: bi(
      "Genes where one route dominates: mostly loss of function, or mostly missense. It "
      + "decides whether replacing the protein could possibly help.",
      "Genes em que uma rota domina: sobretudo perda de função, ou sobretudo missense. Isso "
      + "decide se repor a proteína poderia ajudar.",
    ),
  },

  filterPlaceholder: bi("filter these classes…", "filtrar estas classes…"),
  noMatch: bi("No class matches that.", "Nenhuma classe corresponde."),
  pickOne: bi(
    "Choose a class on the left to see its genes.",
    "Escolha uma classe à esquerda para ver os genes dela.",
  ),
  showing: bi("— showing {shown} of {total}", "— mostrando {shown} de {total}"),
  belowFloor: bi(
    "{n} more classes hold fewer than {min} genes each and are not offered as a way in. They "
    + "are not hidden from the data — only from this list, where a three-gene class is a "
    + "curiosity rather than a route.",
    "Outras {n} classes têm menos de {min} genes cada e não são oferecidas como entrada. Não "
    + "estão escondidas do dado — só desta lista, onde uma classe de três genes é curiosidade "
    + "e não caminho.",
  ),
  absent: bi(
    "The facet index has not been generated.",
    "O índice de facetas não foi gerado.",
  ),
} as const;
