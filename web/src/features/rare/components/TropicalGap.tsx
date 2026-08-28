import { useMemo } from "react";
import raw from "../../../data/generated/tropical_gap.json";
import { useT, fill } from "../../../i18n";
import { TROP } from "../../../i18n/tropical";
import { fmtInt } from "../../../lib/scale";
import css from "./TropicalGap.module.css";

/** WHAT THE CATALOGUES DO NOT SEE.
 *
 *  Every layer of this site reads three files: HPO's phenotype annotations, HPO's
 *  gene-to-disease table, Orphanet's prevalence. They are catalogues of Mendelian and rare
 *  disease, by charter. Nobody promised they would describe malaria.
 *
 *  That is the point. The ontologies and joins the whole field builds on inherit a shape, and
 *  a disease caused by a parasite, a virus or a vector does not fit it — so it arrives as
 *  ABSENT rather than as OUT OF SCOPE, and every method downstream cannot tell the two apart.
 *  A clinician in Belém looking up Chagas disease in a genomics tool finds nothing, and
 *  nothing on the screen explains why.
 *
 *  THE COMPARISON IS THE ARGUMENT. A zero proves nothing alone. Beside it sits the same
 *  measure over the twelve rare Mendelian diseases this repository profiles in depth — rare
 *  by definition, several ultra-rare, and exactly what these catalogues exist for. Schisto-
 *  somiasis reaches over two hundred million people and has fewer phenotype rows than a
 *  disease with a few thousand cases.
 */

type Row = {
  name: string;
  mondoTerms: number;
  xrefIds: number;
  annotations: number;
  signsWithDenominator: number;
  geneLinks: number;
  prevalence: boolean;
};

type Payload = {
  generated: string;
  premise: string;
  listIsAuthored: string;
  groups: Record<string, Row[]>;
  reference: Row[];
  summary: {
    diseases: number;
    namedByMondo: number;
    withNoAnnotation: number;
    silentNames: string[];
    medianAnnotationsTropical: number;
    medianAnnotationsReference: number;
    medianGeneLinksTropical: number;
    medianGeneLinksReference: number;
  };
};

const data = raw as unknown as Payload;

const GROUP_LABEL: Record<string, keyof typeof TROP> = {
  "vector-borne": "gVector",
  "water and soil": "gWater",
  "bacterial and other": "gBacterial",
  "respiratory pandemic": "gRespiratory",
};

export function TropicalGap() {
  const t = useT();
  const s = data.summary;

  // The widest annotation count sets the bar scale, and the reference set is included in it
  // deliberately: two charts on two scales would hide the very comparison being made.
  const peak = useMemo(() => Math.max(
    ...Object.values(data.groups).flat().map((d) => d.annotations),
    ...data.reference.map((d) => d.annotations), 1,
  ), []);

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{s.withNoAnnotation}</span>
        <p>
          {fill(t(TROP.headline), { n: s.namedByMondo })}{" "}
          <strong>{t(TROP.headlineStrong)}</strong>{" "}
          {t(TROP.headlineTail)}
        </p>
      </div>

      <div className={css.compare}>
        <Stat k={t(TROP.mAnnotations)} a={s.medianAnnotationsTropical}
              b={s.medianAnnotationsReference}
              la={t(TROP.setTropical)} lb={t(TROP.setReference)} />
        <Stat k={t(TROP.mGenes)} a={s.medianGeneLinksTropical}
              b={s.medianGeneLinksReference}
              la={t(TROP.setTropical)} lb={t(TROP.setReference)} />
      </div>

      <p className={css.premise}>{t(TROP.premise)}</p>

      {Object.entries(data.groups).map(([key, rows]) => (
        <section key={key} className={css.group}>
          <h4 className={css.groupName}>
            {GROUP_LABEL[key] ? t(TROP[GROUP_LABEL[key]] as never) : key}
          </h4>
          <ul className={css.rows}>
            {rows.map((d) => (
              <DiseaseRow key={d.name} d={d} peak={peak} />
            ))}
          </ul>
        </section>
      ))}

      <section className={css.group}>
        <h4 className={css.groupName}>{t(TROP.gReference)}</h4>
        <p className={css.groupNote}>{t(TROP.referenceNote)}</p>
        <ul className={css.rows}>
          {data.reference.map((d) => (
            <DiseaseRow key={d.name} d={d} peak={peak} reference />
          ))}
        </ul>
      </section>

      <p className={css.caveat}>{t(TROP.authored)}</p>
      <p className={css.caveat}>
        {data.listIsAuthored} <code>{data.generated}</code>
      </p>
    </div>
  );
}

function DiseaseRow({ d, peak, reference }: { d: Row; peak: number; reference?: boolean }) {
  const t = useT();
  const named = d.mondoTerms > 0;
  return (
    <li className={named ? css.row : css.rowUnnamed}>
      <span className={css.name}>
        {d.name}
        {!named && <span className={css.tag}>{t(TROP.notNamed)}</span>}
      </span>

      {/* Length on a common baseline, tropical and reference on the SAME scale. Two charts
          on two scales would hide the comparison the panel exists to make. */}
      <span className={css.track}>
        <span className={reference ? css.barRef : css.bar}
              style={{ width: `${Math.max(d.annotations ? 0.6 : 0, (d.annotations / peak) * 100)}%` }} />
      </span>
      <span className={css.count}>{fmtInt(d.annotations)}</span>

      {/* Three dots: does it have a gene, a sign with a denominator, a prevalence. These are
          the three fields every other panel on this site assumes exist. */}
      <span className={css.dots} aria-hidden="true">
        <i className={d.geneLinks ? css.dotOn : css.dotOff} title="gene" />
        <i className={d.signsWithDenominator ? css.dotOn : css.dotOff} title="denominator" />
        <i className={d.prevalence ? css.dotOn : css.dotOff} title="prevalence" />
      </span>
    </li>
  );
}

function Stat(
  { k, a, b, la, lb }: { k: string; a: number; b: number; la: string; lb: string },
) {
  const peak = Math.max(a, b, 1);
  return (
    <div className={css.stat}>
      <span className={css.statK}>{k}</span>
      <span className={css.statRow}>
        <span className={css.statLabel}>{la}</span>
        <span className={css.statTrack}>
          <span className={css.statBar} style={{ width: `${(a / peak) * 100}%` }} />
        </span>
        <span className={css.statVal}>{fmtInt(a)}</span>
      </span>
      <span className={css.statRow}>
        <span className={css.statLabel}>{lb}</span>
        <span className={css.statTrack}>
          <span className={css.statBarRef} style={{ width: `${(b / peak) * 100}%` }} />
        </span>
        <span className={css.statVal}>{fmtInt(b)}</span>
      </span>
    </div>
  );
}
