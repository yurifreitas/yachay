import { useState } from "react";
import raw from "../../../data/generated/trait_atlas.json";
import { useT } from "../../../i18n";
import { SAMP } from "../../../i18n/sampled";
import { fmtInt } from "../../../lib/scale";
import { Provenance } from "./Provenance";
import css from "./MeasuredPanels.module.css";
import own from "./TraitAtlas.module.css";

/** EIGHT DISEASE AREAS ON FIVE AXES — and what the comparison did to the claim before it.
 *
 *  `psychiatric_gwas` reported psychiatric samples 65.8 % European and invited a reader to
 *  conclude that psychiatric genetics has a representativeness problem. Put beside the other
 *  seven areas, psychiatry is the LEAST European of the eight: cancer is 80.8 %, and the
 *  residual "other disease" bucket 83.5 %. The problem is not psychiatry's; it is the field's,
 *  and psychiatry is the part of it doing best.
 *
 *  That reversal is the whole reason this panel exists, and it is why the layout is parallel
 *  coordinates rather than eight bar charts. The five axes are different KINDS of quantity —
 *  three shares, a median size, a count — so there is no plane two of them could share. What
 *  a reader needs to see is whether the polylines are PARALLEL: eight areas that rise and
 *  fall together are one field with one problem, and eight that cross are eight problems.
 *
 *  ADR 0008: every position here was solved in Python. The browser draws coordinates; it does
 *  not decide an order, a normalisation or a seriation, because each of those is an argument
 *  and an argument belongs where it can be tested.
 */

const d = raw as any;
const pct = (v: number, p = 1) => `${(100 * v).toFixed(p)} %`;

/* ------------------------------------------------------------------ parallel coordinates */

export function TraitAxes() {
  const tt = useT();
  const pcp = d.layout?.pcp ?? {};
  const axes: any[] = pcp.axes ?? [];
  const lines: any[] = pcp.lines ?? [];
  const [hover, setHover] = useState<string | null>(null);
  const verdict = d.what_the_comparison_did_to_the_earlier_claim ?? {};

  const x = (i: number) => (axes.length < 2 ? 50 : (i / (axes.length - 1)) * 100);
  const y = (v: number) => 100 - v * 100;

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(verdict.range?.spread ?? 0)}</span>
        <p>
          <span className={css.answersK}>{tt(SAMP.pcpHeading)}</span>
          {verdict.reading}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.pcpAxes)}</span>
        <p className={css.blockSub}>{pcp.reading}</p>

        <div className={own.pcpWrap}>
          <div className={own.pcp}>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className={own.svg}
                 role="img" aria-label={tt(SAMP.pcpAria)}>
              {axes.map((_a, i) => (
                <line key={i} x1={x(i)} y1="0" x2={x(i)} y2="100"
                      className={own.axis} vectorEffect="non-scaling-stroke" />
              ))}
              {lines.map((l) => (
                <polyline
                  key={l.area}
                  points={l.at.map((v: number, i: number) => `${x(i)},${y(v)}`).join(" ")}
                  className={hover && hover !== l.area ? own.lineDim : own.line}
                  vectorEffect="non-scaling-stroke"
                  onPointerEnter={() => setHover(l.area)}
                  onPointerLeave={() => setHover(null)}
                />
              ))}
            </svg>
            {axes.map((a, i) => (
              <span key={a.key} className={own.axisLabel}
                    style={{ left: `${x(i)}%`,
                             transform: i === 0 ? "translateX(0)"
                               : i === axes.length - 1 ? "translateX(-100%)"
                               : "translateX(-50%)" }}>
                {a.label}
                <span className={own.axisRange}>
                  {a.kind === "share" ? pct(a.min, 0) : fmtInt(a.min)} –{" "}
                  {a.kind === "share" ? pct(a.max, 0) : fmtInt(a.max)}
                </span>
              </span>
            ))}
          </div>
        </div>

        {/* The legend is a table of the raw values, not a colour key. Eight near-identical
            polylines cannot be told apart by hue, and the numbers are what a reader would
            check anyway. Hovering a row lights its line. */}
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>disease area</th>
                {axes.map((a) => <th key={a.key}>{a.label.split(" ").slice(0, 2).join(" ")}</th>)}
              </tr>
            </thead>
            <tbody>
              {lines.map((l) => (
                <tr key={l.area}
                    className={hover === l.area ? own.rowOn : undefined}
                    onPointerEnter={() => setHover(l.area)}
                    onPointerLeave={() => setHover(null)}>
                  <td className={css.tdName}>{l.area}</td>
                  {axes.map((a) => (
                    <td key={a.key} className={css.tdMuted}>
                      {a.kind === "share" ? pct(l.raw[a.key]) : fmtInt(l.raw[a.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.pcpCategories)}</span>
        <p className={css.caveat}>{d.categories?.why_not_authored}</p>
        <p className={css.note}>
          Measurement terms are excluded from the disease comparison and reported separately:{" "}
          {(d.categories?.measurement_terms_excluded ?? []).join(", ")}. Letting 86,375 rows of
          &ldquo;other measurement&rdquo; into a comparison of diseases would drown it.
        </p>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.categories}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ------------------------------------------------------------------ seriated matrix */

export function TraitMatrix() {
  const tt = useT();
  const m = d.layout?.matrix ?? {};
  const rows: string[] = m.rows ?? [];
  const cols: string[] = m.cols ?? [];
  const values: number[][] = m.values ?? [];
  const max = Math.max(0.0001, ...values.flat());

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{rows.length}×{cols.length}</span>
        <p>
          <span className={css.answersK}>{tt(SAMP.matHeading)}</span>
          {m.reading}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(SAMP.matSeriated)}</span>
        <div className={own.matWrap}>
          <table className={own.mat}>
            <thead>
              <tr>
                <th />
                {cols.map((c) => (
                  <th key={c}><span className={own.colHead}>{c}</span></th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r}>
                  <th scope="row" className={own.rowHead}>{r}</th>
                  {cols.map((c, j) => {
                    const v = values[i]?.[j] ?? 0;
                    return (
                      // The value is printed in every cell that has one. A heat cell alone
                      // asks the reader to read a colour back into a number, which is the
                      // step this project's own visualisation notes say to avoid when the
                      // grid is small enough to carry text.
                      <td key={c} className={own.cell}
                          style={{ "--v": v / max } as React.CSSProperties}
                          title={`${r} · ${c}: ${pct(v, 2)}`}>
                        <span className={own.cellV}>
                          {v >= 0.005 ? (100 * v).toFixed(v >= 0.1 ? 0 : 1) : ""}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>
          Cells are percentages of analysis weight. Both axes are ordered by the seriation
          solved in <code>tools/trait_atlas.py</code>, not alphabetically — the row order is
          the argument that these areas group.
        </p>
      </div>
    </div>
  );
}
