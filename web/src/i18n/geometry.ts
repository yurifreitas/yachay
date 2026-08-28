/** The molecular-geometry panels, in both languages. */
import type { Bi } from "./types";

const bi = (en: string, pt: string): Bi => ({ en, pt });

export const GEO = {
  gShape: bi("The shape of the damage", "A forma do dano"),
  qShape: bi(
    "Where along the molecule the variants fall, by what route they break it, and whether "
    + "the damage is concentrated or everywhere.",
    "Onde ao longo da molécula as variantes caem, por qual rota elas o quebram, e se o dano "
    + "é concentrado ou está em toda parte.",
  ),

  sNeedle: bi("Where the variants fall", "Onde as variantes caem"),
  sRoutes: bi("How it breaks", "Como ele quebra"),
  sPathways: bi("What it operates in", "Em que ele opera"),

  /* ------------------------------------------------------------------ needle */
  needleLede: bi(
    "The horizontal axis is the protein itself, residue 1 to the last. A needle stands where "
    + "variants were reported and its height is how many. Every variant panel elsewhere on "
    + "this site is a total, and a total cannot tell apart the two situations that matter "
    + "most: damage concentrated in eighty residues of one interface, and damage spread "
    + "evenly along two thousand. Those are different diseases and their totals are identical.",
    "O eixo horizontal é a própria proteína, do resíduo 1 até o último. Uma agulha se ergue "
    + "onde variantes foram reportadas e a altura dela é quantas. Todo painel de variantes "
    + "no resto deste site é um total, e um total não distingue as duas situações que mais "
    + "importam: dano concentrado em oitenta resíduos de uma interface, e dano espalhado por "
    + "dois mil. São doenças diferentes e os totais são idênticos.",
  ),
  needleRead: bi(
    "Pathogenic sits on the baseline, where the shape of the profile can be read; uncertain "
    + "stacks above it, where its bulk is obvious without competing for the axis. The dashed "
    + "markers are residues hit more than once — a residue reported two hundred times is a "
    + "fact about the gene, not a rounding.",
    "As patogênicas ficam na linha de base, onde a forma do perfil pode ser lida; as "
    + "incertas se empilham acima, onde o volume delas é óbvio sem disputar o eixo. Os "
    + "marcadores tracejados são resíduos atingidos mais de uma vez — um resíduo reportado "
    + "duzentas vezes é um fato sobre o gene, não um arredondamento.",
  ),
  axis: bi("residue along the protein", "resíduo ao longo da proteína"),
  residues: bi("residues", "resíduos"),
  placed: bi("variants placed on the sequence", "variantes posicionadas na sequência"),
  lPathogenic: bi("pathogenic", "patogênicas"),
  lUncertain: bi("uncertain", "incertas"),
  lBenign: bi("benign", "benignas"),
  lConflicting: bi("conflicting", "conflitantes"),
  lengthFromString: bi("length from STRING", "comprimento do STRING"),

  /* The domain track's own legend. Category, not order. */
  fDomain: bi("folded domain", "domínio dobrado"),
  fMembrane: bi("membrane pass", "trecho transmembrana"),
  fMotif: bi("motif", "motivo"),
  fActive: bi("catalytic residue", "resíduo catalítico"),
  fBinding: bi("binding site", "sítio de ligação"),
  trackLede: bi(
    "The bands under the axis are the parts of the protein, from UniProt's curated features. "
    + "Without them a cluster at residue 340 is a number; with them it is a variant landing "
    + "in a kinase domain, or in a membrane pass a cytosolic drug cannot reach, or in a "
    + "stretch nobody has characterised — and those are three different problems.",
    "As faixas sob o eixo são as partes da proteína, das anotações curadas do UniProt. Sem "
    + "elas um agrupamento no resíduo 340 é um número; com elas é uma variante caindo num "
    + "domínio quinase, ou num trecho transmembrana que um fármaco citosólico não alcança, "
    + "ou num trecho que ninguém caracterizou — e são três problemas diferentes.",
  ),
  trackCaution: bi(
    "UniProt features are curated: a protein with no annotated part is usually one nobody "
    + "has characterised, not one without structure. That is the same attention bias the VUS "
    + "share measures, one layer down. Coverage is 74% of the genes in this navigator.",
    "As anotações do UniProt são curadas: uma proteína sem parte anotada em geral é uma que "
    + "ninguém caracterizou, não uma sem estrutura. É o mesmo viés de atenção que a fração "
    + "de VUS mede, uma camada abaixo. A cobertura é de 74% dos genes deste navegador.",
  ),
  lengthFromObserved: bi(
    "length inferred from the variants themselves — a weaker axis",
    "comprimento inferido das próprias variantes — um eixo mais fraco",
  ),

  /* -------------------------------------------------------------- clustering */
  clusterTitle: bi("Is the hotspot real, or is it looking?", "O ponto quente é real, ou é o olhar?"),
  clusterHead: bi(
    "{share} of the pathogenic variants fall in the densest tenth of the protein — {ratio}× "
    + "what an even spread would put there.",
    "{share} das variantes patogênicas caem no décimo mais denso da proteína — {ratio}× o "
    + "que uma distribuição uniforme colocaria ali.",
  ),
  clusterFlat: bi(
    "The damage is spread: no tenth of this protein carries appreciably more than its share. "
    + "A gene that breaks everywhere is usually one that breaks by being absent rather than "
    + "by being altered.",
    "O dano está espalhado: nenhum décimo desta proteína carrega apreciavelmente mais do que "
    + "lhe caberia. Um gene que quebra em toda parte costuma ser um que quebra por estar "
    + "ausente, não por estar alterado.",
  ),
  clusterCaution: bi(
    "Variant density tracks sequencing depth and curation attention as well as biology. Exons "
    + "are not sequenced equally and well-studied regions accumulate reports. A spike is "
    + "evidence of a hotspot OR of a well-studied stretch, and nothing measured here can "
    + "separate the two.",
    "A densidade de variantes acompanha profundidade de sequenciamento e atenção de "
    + "curadoria tanto quanto biologia. Éxons não são sequenciados igualmente e regiões bem "
    + "estudadas acumulam relatos. Um pico é evidência de um ponto quente OU de um trecho bem "
    + "estudado, e nada medido aqui separa os dois.",
  ),
  clusterTooFew: bi(
    "Fewer than ten pathogenic variants have been placed on the sequence — too few to say "
    + "anything about concentration.",
    "Menos de dez variantes patogênicas foram posicionadas na sequência — poucas demais para "
    + "dizer algo sobre concentração.",
  ),
  aNeedle: bi(
    "No variant in ClinVar for this gene carries a protein position. That happens when the "
    + "reported variants are intronic, structural, or predate the HGVS conventions the "
    + "position is parsed from.",
    "Nenhuma variante do ClinVar para este gene carrega posição na proteína. Isso acontece "
    + "quando as variantes reportadas são intrônicas, estruturais, ou anteriores às "
    + "convenções HGVS de onde a posição é lida.",
  ),

  /* ------------------------------------------------------------------ routes */
  routesLede: bi(
    "The routes by which this gene breaks, and they are not interchangeable. A gene damaged "
    + "mostly by stop-gained and frameshift variants is losing its protein; one damaged "
    + "almost entirely by missense is more often losing a specific function, or gaining one. "
    + "That distinction decides whether replacing the protein could possibly help.",
    "As rotas pelas quais este gene quebra, e elas não são intercambiáveis. Um gene "
    + "danificado sobretudo por variantes de códon de parada e mudança de matriz está "
    + "perdendo sua proteína; um danificado quase só por missense está mais frequentemente "
    + "perdendo uma função específica, ou ganhando uma. Essa distinção decide se repor a "
    + "proteína poderia sequer ajudar.",
  ),
  rMissense: bi("Missense", "Missense"),
  rStopGained: bi("Stop gained", "Códon de parada ganho"),
  rStopLost: bi("Stop lost", "Códon de parada perdido"),
  rFrameshift: bi("Frameshift", "Mudança de matriz"),
  rSplice: bi("Splice site", "Sítio de splicing"),
  rInFrameIndel: bi("In-frame indel", "Indel em matriz"),
  rSynonymous: bi("Synonymous", "Sinônima"),
  rStructural: bi("Structural", "Estrutural"),
  rOther: bi("Other", "Outras"),

  /* ---------------------------------------------------------------- pathways */
  pathwaysLede: bi(
    "Reactome pathways this protein is annotated to. This is the closest honest answer this "
    + "repository can give offline to 'which signalling does it operate in' — and its limit "
    + "matters: pathway membership is a statement about the protein, not about which of its "
    + "residues carry the signal. Nothing here says where on the molecule a signalling region "
    + "begins, and any interface that implied otherwise would be inventing structure.",
    "Vias do Reactome às quais esta proteína está anotada. É a resposta honesta mais próxima "
    + "que este repositório consegue dar offline para \"em qual sinalização ele opera\" — e o "
    + "limite importa: pertencer a uma via é uma afirmação sobre a proteína, não sobre quais "
    + "resíduos dela carregam o sinal. Nada aqui diz onde na molécula começa uma região de "
    + "sinalização, e qualquer interface que sugerisse o contrário estaria inventando "
    + "estrutura.",
  ),
  pathwayCount: bi("Pathways", "Vias"),
  pathwayCountSub: bi("Reactome, human only", "Reactome, apenas humano"),
  pTruncated: bi("Showing the first of", "Mostrando as primeiras de"),
  aPathways: bi(
    "No Reactome pathway is annotated to this protein. In a database that reaches about a "
    + "third of the proteome, absence is as much a statement about curation coverage as about "
    + "the protein.",
    "Nenhuma via do Reactome está anotada a esta proteína. Num banco que alcança cerca de um "
    + "terço do proteoma, a ausência é tanto uma afirmação sobre cobertura de curadoria "
    + "quanto sobre a proteína.",
  ),

  /* ------------------------------------------------------------------ layers */
  layerGeo: bi("Molecular geometry", "Geometria molecular"),
  layerGeoHas: bi("{n} variants placed", "{n} variantes posicionadas"),
  layerGeoNone: bi("no variant carries a position", "nenhuma variante carrega posição"),
} as const;
