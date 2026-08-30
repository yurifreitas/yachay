import raw from "../../data/generated/obesity_thermogenesis.json";
import type { SectionRegistry } from "../../lib/sectionRegistry";
import type { Text } from "../../i18n";
import { useT } from "../../i18n";
import { DISC } from "../../i18n/discovery";
import { Provenance } from "../rare/components/Provenance";
import { fmtInt } from "../../lib/scale";
import css from "../rare/components/MeasuredPanels.module.css";
import own from "./DiscoveryPage.module.css";

/** The obesity screen, in four panels.
 *
 *  The order is the argument: the gate that let this be measured at all, the control pool
 *  that made the null resampleable, the floor that control produces at each cell count, and
 *  only then what the floor does to the ranking. Putting the ranking first would let a reader
 *  take the re-ordering on trust, which is the thing this whole library is against.
 */

const d = raw as any;
const f3 = (v: number) => v.toFixed(3);

/* ------------------------------------------------------------------ the gate */

function Fit() {
  const t = d.fit_test ?? {};
  const sc = d.scale ?? {};
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>4/4</span>
        <p>
          <span className={css.answersK}>the four-question fit test</span>
          {d.question}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>answered in writing before any code was run</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <tbody>
              {[["entity", t.entity], ["observation", t.observation],
                ["aggregate", t.aggregate], ["counts vary", t.counts_vary]].map(([k, v]) => (
                <tr key={k as string}>
                  <td className={css.tdName}>{k}</td>
                  <td className={css.tdMuted}>{v as string}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>{t.verdict}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>the screen</span>
        <div className={css.pair}>
          {[["perturbations", sc.perturbations], ["cells scored", sc.cells_scored],
            ["signatures", sc.signatures], ["control cells", sc.control_cells]].map(([k, v]) => (
            <div key={k as string} className={css.stat}>
              <span className={css.statVal}>{fmtInt(Number(v ?? 0))}</span>
              <span className={css.statK}>{k as string}</span>
            </div>
          ))}
        </div>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.fit_test}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ------------------------------------------------------------------ the control pool */

function Control() {
  const c = d.control_pool ?? {};
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>1/3</span>
        <p>
          <span className={css.answersK}>{c.rank}</span>
          {c.used}
        </p>
      </div>
      <div className={css.block}>
        <span className={css.blockK}>why a designed control changes what can be claimed</span>
        <p className={css.blockSub}>{c.why_it_matters}</p>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>{fmtInt(c.cells ?? 0)}</span>
            <span className={css.statK}>cells perturbed with nothing</span>
            <span className={css.statNote}>
              enough to resample the statistic at every cell count a real perturbation has
            </span>
          </div>
        </div>
      </div>
      <p className={css.caveat}>{(d.limits ?? [])[2]}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ the floor */

function Floor() {
  const rows: any[] = d.null_by_count ?? [];
  const top = Math.max(...rows.map((r) => r.p99), 0.001);
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>
          {f3(rows[0]?.null_mean ?? 0)}
          <span className={css.unit}>at {rows[0]?.cells} cells</span>
        </span>
        <p>
          <span className={css.answersK}>what zero is worth</span>
          The same statistic on cells perturbed with nothing. At{" "}
          {rows[rows.length - 1]?.cells} cells the floor is{" "}
          {f3(rows[rows.length - 1]?.null_mean ?? 0)} — so &ldquo;zero&rdquo; moves by more
          than tenfold across the range this screen actually contains.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>the floor, and the bar to clear it, by cell count</span>
        {/* Three lines on one baseline: the floor, and the two percentiles a claim has to
            clear. Drawn as bars per count rather than as a curve because the counts are the
            fitted grid and interpolating between them in the picture would imply a
            smoothness the fit does not have. */}
        <div className={css.rows}>
          {rows.map((r) => (
            <div key={r.cells} className={css.row}>
              <span className={css.rowLabel}>{r.cells} cells</span>
              <span className={own.floorTrack}>
                <span className={own.floorP99} style={{ width: `${(100 * r.p99) / top}%` }} />
                <span className={own.floorP95} style={{ width: `${(100 * r.p95) / top}%` }} />
                <span className={own.floorMean}
                      style={{ width: `${(100 * r.null_mean) / top}%` }} />
              </span>
              <span className={css.rowVal}>{f3(r.null_mean)}</span>
              <span className={css.rowNote}>p95 {f3(r.p95)}</span>
            </div>
          ))}
        </div>
        <p className={css.note}>
          Solid is the mean of the control resample; the two lighter extents behind it are its
          95th and 99th percentiles. A perturbation scoring below the light bar at its own cell
          count has produced nothing a non-targeting guide does not produce.
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ the reranking */

function Rerank() {
  const t = useT();
  const r = d.reranking ?? {};
  const rows: any[] = d.rows ?? [];
  const raw20: string[] = r.raw_top20 ?? [];
  const cal20: string[] = r.calibrated_top20 ?? [];
  const byGene = Object.fromEntries(rows.map((x: any) => [x.gene, x]));
  const u = d.uncertainty ?? {};
  const displaced = raw20.filter((g) => !cal20.includes(g));
  const promoted = cal20.filter((g) => !raw20.includes(g));

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{r.displaced}</span>
        <p>
          <span className={css.answersK}>of the raw top twenty, displaced</span>
          The competition's own ordering against the same ordering with each perturbation
          judged at its own cell count. Sixteen of twenty survive, which is a result about the
          aggregate being reasonably robust — and four do not.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>what the calibration moved</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statK}>dropped out of the top twenty</span>
            {displaced.map((g) => (
              <span key={g} className={css.statNote}>
                {g} · {byGene[g]?.cells} cells · z {byGene[g]?.z}
              </span>
            ))}
          </div>
          <div className={css.stat}>
            <span className={css.statK}>rose into it</span>
            {promoted.map((g) => (
              <span key={g} className={css.statNote}>
                {g} · {byGene[g]?.cells} cells · z {byGene[g]?.z}
              </span>
            ))}
          </div>
        </div>
        <p className={css.note}>
          Perturbations under {r.small_n_threshold} cells in the raw top twenty:{" "}
          <strong>{r.small_n_in_raw_top20}</strong>. After calibration:{" "}
          <strong>{r.small_n_in_calibrated_top20}</strong>. That is the direction the
          correction is supposed to move things.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>the calibrated ranking</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>perturbation</th><th>cells</th><th>raw</th>
                <th>floor at that n</th><th>z</th><th>z interval</th><th>clears p95</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 20).map((x: any) => (
                <tr key={x.gene}>
                  <td className={css.tdName}>{x.gene}</td>
                  <td className={css.tdMuted}>{x.cells}</td>
                  <td>{f3(x.raw)}</td>
                  <td className={css.tdMuted}>{f3(x.null_mean)}</td>
                  <td>{x.z}</td>
                  <td className={css.tdMuted}>
                    {x.z_ci95 ? `${x.z_ci95[0]} – ${x.z_ci95[1]}` : "—"}
                  </td>
                  {/* "yes" only when the INTERVAL clears it. A point estimate that clears a
                      95th percentile and an interval that does are different claims, and the
                      column used to make only the weaker one. */}
                  <td className={x.interval_clears_p95 ? css.tdName : css.tdMuted}>
                    {x.interval_clears_p95 ? "yes" : x.above_null_p95 ? "point only" : "no"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* THE HARDER NUMBER, and it belongs in the ranking panel rather than in a footnote.
          A z says how far a score sits from its null. It says nothing about how far the score
          itself would move if the same perturbation were sequenced again — and that is the
          question a reader deciding what to put on a bench actually has. */}
      <div className={css.block}>
        <span className={css.blockK}>{t(DISC.uncertaintyK)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>{u.clear_p95_on_the_point}</span>
            <span className={css.statK}>clear the null on the point estimate</span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{u.clear_p95_on_the_interval}</span>
            <span className={css.statK}>clear it on the lower end of their own interval</span>
            <span className={css.statNote}>
              the ones that would survive being sequenced again from a different sample of the
              same cells
            </span>
          </div>
          <div className={`${css.stat}`}>
            <span className={`${css.statVal} ${css.valueMuted}`}>{u.point_only}</span>
            <span className={css.statK}>clear it on the point alone</span>
          </div>
        </div>
        <p className={css.note}>{u.reading}</p>
        <p className={css.caveat}>{u.why_not_percentile}</p>
      </div>

      <p className={css.caveat}>{d.says}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ registry */

export type DiscoveryCtx = { tt: (t: Text) => string };

export const DISCOVERY_SECTIONS: SectionRegistry<DiscoveryCtx> = [
  {
    id: "fit",
    title: (ctx) => (<>{ctx.tt(DISC.fitHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DISC.fitSub)}</>),
    view: () => (<><Fit /></>),
  },
  {
    id: "control",
    title: (ctx) => (<>{ctx.tt(DISC.controlHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DISC.controlSub)}</>),
    view: () => (<><Control /></>),
  },
  {
    id: "nullfloor",
    title: (ctx) => (<>{ctx.tt(DISC.floorHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DISC.floorSub)}</>),
    view: () => (<><Floor /></>),
  },
  {
    id: "rerank",
    title: (ctx) => (<>{ctx.tt(DISC.rerankHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DISC.rerankSub)}</>),
    view: () => (<><Rerank /></>),
  },
];
