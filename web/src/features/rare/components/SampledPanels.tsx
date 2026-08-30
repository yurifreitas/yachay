import raw from "../../../data/generated/psychiatric_gwas.json";
import { useT } from "../../../i18n";
import { SAMP } from "../../../i18n/sampled";
import { fmtInt } from "../../../lib/scale";
import { Provenance } from "./Provenance";
import css from "./MeasuredPanels.module.css";

/** WHO WAS IN THE SAMPLE — and why this lives beside gene_constraint rather than in a pillar.
 *
 *  Several results on this site carry a caveat that their panels are not ancestry-neutral.
 *  `tools/gene_constraint.py` states it plainly: gnomAD's reference population is majority
 *  European, so constraint is estimated where the variation was sampled. That has been a
 *  disclaimer — the kind of sentence a reader skims because it appears under every result and
 *  changes nothing about any of them.
 *
 *  The GWAS Catalogue turns it into a count, on the disorders where samples are largest and
 *  the statistical machinery is strongest, which is exactly where a reader would expect the
 *  problem to be smallest. It is not.
 *
 *  WHAT THESE PANELS DO NOT SAY, and the distinction carries the whole section: nothing here
 *  claims a finding is false. A genome-wide significant association from a European cohort is
 *  established in that population. Whether it transfers is a separate question these data do
 *  not touch. The claim is narrower and harder to argue with: this is who it was established
 *  in, counted.
 */

const d = raw as any;
const pct = (v: number, p = 1) => `${(100 * v).toFixed(p)} %`;

/* ------------------------------------------------------------------ composition */

export function SampleAncestry() {
  const tt = useT();
  const o = d.overall ?? {};
  const rows: any[] = o.by_weight ?? [];
  const top = rows[0]?.share || 1;
  const sc = d.scale ?? {};

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(o.european_share ?? 0)}</span>
        <p>
          <span className={css.answersK}>{tt(SAMP.ancHeading)}</span>
          {d.question}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.ancWeight)}</span>
        <div className={css.rows}>
          {rows.map((r) => (
            <div key={r.ancestry} className={css.row}>
              <span className={css.rowLabel}>{r.ancestry}</span>
              <span className={css.track}>
                <span className={r.ancestry === "NR" ? css.barRef : css.bar}
                      style={{ width: `${(100 * r.share) / top}%` }} />
              </span>
              <span className={css.rowVal}>{pct(r.share, 2)}</span>
            </div>
          ))}
        </div>
        <p className={css.note}>
          {fmtInt(sc.psychiatric_accessions ?? 0)} analyses, median sample{" "}
          {fmtInt(sc.median_individuals_per_analysis ?? 0)}, largest{" "}
          {fmtInt(sc.largest_analysis ?? 0)}. Each analysis contributes weight 1, split across
          the ancestries it reports — see the third panel for why it is not a count of people.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.ancUnstated)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>{pct(o.unstated_share ?? 0)}</span>
            <span className={css.statK}>of analysis weight states no ancestry</span>
            <span className={css.statNote}>
              counted as its own category rather than distributed across the others — a field
              not saying who it studied is a result about the field
            </span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{o.african_majority_analyses ?? 0}</span>
            <span className={css.statK}>
              of {fmtInt(o.analyses ?? 0)} analyses have an African-ancestry majority
            </span>
          </div>
        </div>
      </div>

      <p className={css.caveat}>{d.says}</p>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.unit}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ------------------------------------------------------------------ per disorder */

export function SampleDisorders() {
  const tt = useT();
  const entries = Object.entries(d.by_disorder ?? {}) as [string, any][];
  const ordered = [...entries].sort((a, b) => b[1].accessions - a[1].accessions);
  const countries: any[] = d.commonest_countries_of_recruitment ?? [];
  const topC = countries[0]?.analyses || 1;
  const zero = ordered.filter(([, v]) => !v.african_majority_analyses).length;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>{zero}</span>
        <p>
          <span className={css.answersK}>{tt(SAMP.disHeading)}</span>
          {tt(SAMP.disSub)}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.disTable)}</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>disorder</th><th>analyses</th><th>median n</th>
                <th>European</th><th>unstated</th><th>African majority</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map(([name, v]) => (
                <tr key={name}>
                  <td className={css.tdName}>{name}</td>
                  <td>{fmtInt(v.accessions)}</td>
                  <td className={css.tdMuted}>{fmtInt(v.median_individuals ?? 0)}</td>
                  <td>{pct(v.european_share)}</td>
                  <td className={css.tdMuted}>{pct(v.unstated_share)}</td>
                  {/* Zero is drawn as a word, not as a digit that scans like any other
                      number in the column. It is the finding. */}
                  <td className={v.african_majority_analyses ? undefined : css.tdName}>
                    {v.african_majority_analyses ? v.african_majority_analyses : "none"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>
          Selected by MONDO term at the accession level, not by matching text against a trait
          field. The ids are listed in <code>tools/psychiatric_gwas.py</code> so the boundary
          is inspectable and arguable.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.disCountries)}</span>
        <div className={css.rows}>
          {countries.slice(0, 14).map((c) => (
            <div key={c.country} className={css.row}>
              <span className={css.rowLabel}>{c.country}</span>
              <span className={css.track}>
                <span className={css.bar}
                      style={{ width: `${(100 * c.analyses) / topC}%` }} />
              </span>
              <span className={css.rowVal}>{fmtInt(c.analyses)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ the two joins */

/** THE CORRECTIONS, AT THE SIZE OF THE RESULT.
 *
 *  Two versions of this measurement were wrong before one was right, and both are worth a
 *  reader's time for the same reason: the second was caught ONLY because it was surprising.
 *  An error of the same kind that had landed at a plausible magnitude would have shipped, and
 *  a site that publishes findings should say that out loud rather than present the third
 *  attempt as though it were the first.
 */
export function SampleJoins() {
  const tt = useT();
  const unit = d.unit ?? {};
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>2</span>
        <p>
          <span className={css.answersK}>{tt(SAMP.joinHeading)}</span>
          {tt(SAMP.joinSub)}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>the arithmetic</span>
        <p className={css.caveat}>{unit.why}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>the join</span>
        <p className={css.caveat}>
          Selecting psychiatric <strong>papers</strong> by trait and taking all their ancestry
          rows imported a phenome-wide study whole — 1,129 accessions, nearly all about
          unrelated traits such as transient cerebral ischemia — because one of its thousands
          of traits was ADHD. It reported ADHD as 81 % East Asian, which contradicts a field
          built on Danish cohorts. The surprise is what got it checked; the fix was to join at
          the accession, the level the ancestry file is actually keyed on. ADHD now reads{" "}
          {pct(d.by_disorder?.ADHD?.european_share ?? 0)} European.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.joinUnit)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statK}>counted</span>
            <span className={css.statNote}>{unit.counted}</span>
          </div>
          <div className={css.stat}>
            <span className={css.statK}>stage</span>
            <span className={css.statNote}>{unit.stage}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
