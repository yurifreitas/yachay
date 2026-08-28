/** The tropical-gap panel, in both languages.
 *
 *  This is the section most likely to be read by someone who lives where these diseases are,
 *  so the Portuguese is not a translation of an English argument — it is the argument, said
 *  the way it would be said in Brazil.
 */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const TROP = {
  section: bi("What the catalogues do not see", "O que os catálogos não enxergam"),
  heading: bi(
    "The diseases that dominate tropical life arrive in these catalogues as absences",
    "As doenças que dominam a vida nos trópicos chegam a estes catálogos como ausências",
  ),
  sub: bi(
    "Every layer of this site reads three files: HPO's phenotype annotations, HPO's "
    + "gene-to-disease table, and Orphanet's prevalence. This asks what those files hold "
    + "about malaria, Chagas disease, schistosomiasis and COVID.",
    "Toda camada deste site lê três arquivos: as anotações de fenótipo do HPO, a tabela "
    + "gene-doença do HPO, e a prevalência do Orphanet. Isto pergunta o que esses arquivos "
    + "guardam sobre malária, doença de Chagas, esquistossomose e COVID.",
  ),

  headline: bi(
    "of the {n} diseases MONDO names,",
    "das {n} doenças que o MONDO nomeia,",
  ),
  headlineStrong: bi(
    "carry no phenotype annotation at all",
    "não carregam nenhuma anotação de fenótipo",
  ),
  headlineTail: bi(
    "— not one recorded sign, onset or inheritance. Among them: schistosomiasis, which "
    + "reaches over two hundred million people; trachoma, the leading infectious cause of "
    + "blindness; onchocerciasis; and long COVID.",
    "— nem um sinal, idade de início ou herança registrados. Entre elas: esquistossomose, "
    + "que atinge mais de duzentos milhões de pessoas; tracoma, principal causa infecciosa "
    + "de cegueira; oncocercose; e COVID longa.",
  ),

  /* --------------------------------------------------------------- the premise */
  premise: bi(
    "HPO and Orphanet are catalogues of Mendelian and rare disease, by charter. Nobody "
    + "promised they would describe malaria — and that is the point rather than the excuse. "
    + "The ontologies and gene-disease joins the entire field builds on inherit a shape, and "
    + "a disease caused by a parasite, a virus or a vector does not fit it. So it arrives as "
    + "ABSENT rather than as OUT OF SCOPE, and no method downstream can tell the two apart. "
    + "A clinician looking up Chagas disease in a genomics tool finds nothing, and nothing on "
    + "the screen explains why.",
    "HPO e Orphanet são catálogos de doença mendeliana e rara, por estatuto. Ninguém "
    + "prometeu que descreveriam malária — e isso é o argumento, não a desculpa. As "
    + "ontologias e as junções gene-doença sobre as quais o campo inteiro constrói herdam uma "
    + "forma, e uma doença causada por um parasita, um vírus ou um vetor não cabe nela. "
    + "Então ela chega como AUSENTE e não como FORA DE ESCOPO, e nenhum método rio abaixo "
    + "distingue as duas coisas. Um clínico que procura doença de Chagas numa ferramenta de "
    + "genômica não encontra nada, e nada na tela explica por quê.",
  ),

  /* ------------------------------------------------------------ the comparison */
  mAnnotations: bi("Median phenotype rows", "Mediana de linhas de fenótipo"),
  mGenes: bi("Median gene links", "Mediana de ligações gene-doença"),
  setTropical: bi("tropical", "tropicais"),
  setReference: bi("rare Mendelian", "raras mendelianas"),

  gVector: bi("Carried by a vector", "Transmitidas por vetor"),
  gWater: bi("Water, soil and food", "Água, solo e alimento"),
  gBacterial: bi("Bacterial and other", "Bacterianas e outras"),
  gRespiratory: bi("Respiratory, pandemic", "Respiratórias, pandêmicas"),
  gReference: bi("The comparison set", "O conjunto de comparação"),
  referenceNote: bi(
    "The twelve rare Mendelian diseases this site profiles in depth. Rare by definition, "
    + "several ultra-rare, and exactly the kind of disease these catalogues exist for. Drawn "
    + "on the same scale as everything above, because two scales would hide the comparison.",
    "As doze doenças raras mendelianas que este site perfila a fundo. Raras por definição, "
    + "várias ultra-raras, e exatamente o tipo de doença para o qual estes catálogos existem. "
    + "Desenhadas na mesma escala de tudo acima, porque duas escalas esconderiam a comparação.",
  ),
  notNamed: bi("not in MONDO", "não está no MONDO"),

  /* ---------------------------------------------------------------- the caveats */
  authored: bi(
    "Three dots per disease: does it have a gene link, a sign with a denominator, a recorded "
    + "prevalence. Those are the three fields every other panel on this site assumes exist.",
    "Três pontos por doença: ela tem ligação com gene, um sinal com denominador, uma "
    + "prevalência registrada. São os três campos que todo outro painel deste site pressupõe "
    + "que existam.",
  ),
} as const;
