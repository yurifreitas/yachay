import { useMemo, useState } from "react";
import { ReadAloud } from "../../atoms/ReadAloud";
import { upset } from "../../../../lib/viz/sets";
import { fmtInt, pct } from "../../../../lib/scale";
import css from "./UpSetPlot.module.css";
import type { UpSetPlotProps } from "./UpSetPlot.types";

/** Which combinations of flags the entities actually carry.
 *
 *  WHY NOT A VENN DIAGRAM. Three circles is the limit at which a Venn stays readable, and
 *  even there the regions encode count by AREA, which is near the bottom of the
 *  Cleveland-McGill order — readers routinely misjudge area by a factor of two. At four sets
 *  a proportional Venn is usually geometrically impossible, so the drawing quietly stops
 *  being proportional and becomes a diagram of the set names.
 *
 *  UpSet (Lex, Gehlenborg, Vuillemot, Streit & Pfister, 2014) inverts the layout: one bar
 *  per INTERSECTION on a common baseline, and a dot matrix underneath naming which
 *  intersection each bar is. Counts are read as length on a shared scale — the encoding
 *  people are best at — and it goes on working at ten sets.
 *
 *  WHAT IT REPAIRS HERE. The rest of this site assigns each entity exactly one class so a
 *  legend can have three colours. That reduction is silently false for anything carrying two
 *  flags, and there was no figure in which the overlap could be seen at all. This is that
 *  figure: if a bar exists over two dots, the single-class colouring elsewhere is hiding
 *  those entities inside whichever class won the tie-break.
 */
export function UpSetPlot({
  count, sets, itemLabel = "entities", labelOf, ariaLabel, readAloud,
  maxCombinations = 12, height = 200,
}: UpSetPlotProps) {
  const result = useMemo(() => upset(count, sets), [count, sets]);
  const [picked, setPicked] = useState<string | null>(null);

  const shown = result.combinations.slice(0, maxCombinations);
  const hidden = result.combinations.length - shown.length;
  const max = shown[0]?.size ?? 1;
  const maxTotal = Math.max(...result.totals.map((t) => t.size), 1);

  if (!shown.length) {
    return (
      <p className={css.absent}>
        None of the {fmtInt(count)} {itemLabel} carries any of these flags, so there are no
        intersections to draw. Said, rather than rendered as an empty grid.
      </p>
    );
  }

  const chosen = shown.find((c) => c.key === picked);

  return (
    <div className={css.wrap}>
      {readAloud && (
        <ReadAloud form="UpSet"
                   source="Lex, Gehlenborg, Vuillemot, Streit & Pfister (2014), IEEE TVCG.">
          {readAloud}
        </ReadAloud>
      )}

      <div className={css.grid} style={{ ["--cols" as string]: shown.length }}>
        {/* --- the intersection bars ------------------------------------------------ */}
        <div className={css.barsCorner} aria-hidden="true" />
        <div className={css.bars} style={{ height }}>
          {shown.map((c) => (
            <button
              key={c.key}
              type="button"
              className={c.key === picked ? css.barOn : css.bar}
              style={{ ["--h" as string]: `${(c.size / max) * 100}%` }}
              onClick={() => setPicked(c.key === picked ? null : c.key)}
              aria-pressed={c.key === picked}
              title={`${c.members.join(" & ")}: ${fmtInt(c.size)}`}
            >
              <span className={css.barValue}>{fmtInt(c.size)}</span>
              <span className={css.barFill} />
            </button>
          ))}
        </div>

        {/* --- the set totals, and the matrix -------------------------------------- */}
        <div className={css.setTotals}>
          {result.totals.map((t) => (
            <div key={t.set} className={css.setRow}>
              <span className={css.setName} title={t.set}>{t.set}</span>
              <span className={css.setBarTrack}>
                <span className={css.setBar} style={{ width: `${(t.size / maxTotal) * 100}%` }} />
              </span>
              <span className={css.setCount}>{fmtInt(t.size)}</span>
            </div>
          ))}
        </div>

        <div className={css.matrix}>
          {sets.map((s) => (
            <div key={s.name} className={css.matrixRow}>
              {shown.map((c) => {
                const on = c.members.includes(s.name);
                return (
                  <span key={c.key}
                        className={on ? css.dotOn : css.dot}
                        data-selected={c.key === picked || undefined}
                        aria-hidden="true" />
                );
              })}
            </div>
          ))}
          {/* The connector: a line through the dots of one column, which is what turns a
              grid of dots into a readable statement about membership. */}
          <div className={css.connectors} aria-hidden="true">
            {shown.map((c) => {
              const idx = sets.map((s, i) => (c.members.includes(s.name) ? i : -1))
                              .filter((i) => i >= 0);
              if (idx.length < 2) return <span key={c.key} />;
              const rows = sets.length;
              return (
                <span key={c.key} className={css.connector}
                      style={{
                        top: `${((idx[0] + 0.5) / rows) * 100}%`,
                        height: `${((idx[idx.length - 1] - idx[0]) / rows) * 100}%`,
                      }} />
              );
            })}
          </div>
        </div>
      </div>

      <p className={css.foot}>
        {fmtInt(result.total)} {itemLabel} in all;{" "}
        <strong>{fmtInt(result.unflagged)}</strong> ({pct(result.unflagged / Math.max(1, result.total), 0)})
        carry none of these flags and are counted here rather than drawn — as a column they
        would be taller than every real intersection and flatten the comparison.
        {hidden > 0 && (
          <> {hidden} smaller intersection{hidden === 1 ? " is" : "s are"} not shown.</>
        )}
      </p>

      {chosen && (
        <div className={css.detail} role="status" aria-live="polite">
          <p>
            <strong>{fmtInt(chosen.size)}</strong> {itemLabel}{" "}
            {chosen.members.length === 1 ? "carry only " : "carry "}
            {chosen.members.map((m, i) => (
              <span key={m}>
                {i > 0 && (i === chosen.members.length - 1 ? " and " : ", ")}
                <em>{m}</em>
              </span>
            ))}
            {chosen.members.length > 1 && " together"}
            {" "}({pct(chosen.size / Math.max(1, result.total), 1)} of all).
          </p>
          {labelOf && (
            <p className={css.members}>
              {chosen.indices.slice(0, 24).map(labelOf).join(", ")}
              {chosen.indices.length > 24 && ` … and ${fmtInt(chosen.indices.length - 24)} more`}
            </p>
          )}
        </div>
      )}

      <span className="visually-hidden">{ariaLabel}</span>
    </div>
  );
}
