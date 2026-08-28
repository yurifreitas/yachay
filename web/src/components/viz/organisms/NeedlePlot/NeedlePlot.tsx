import { useMemo, useState } from "react";
import { PlotFrame } from "../../atoms/PlotFrame";
import { AxisX } from "../../atoms/Axis";
import { ReadAloud } from "../../atoms/ReadAloud";
import { linear, fmtInt } from "../../../../lib/scale";
import css from "./NeedlePlot.module.css";
import type { NeedlePlotProps } from "./NeedlePlot.types";

/** Damage along a molecule, drawn as position rather than as a total.
 *
 *  THE FORM. A lollipop or "needle" plot, the standard in variant interpretation since the
 *  cancer-genomics tools of the early 2010s (MutationMapper, cBioPortal, lollipops). The
 *  horizontal axis is the protein itself, residue 1 to the last; a needle stands where
 *  variants were reported, and its height is how many.
 *
 *  WHY IT REPLACES A COUNT. Every variant panel on this site was a total — 2,565 submitted,
 *  303 pathogenic — and a total cannot distinguish the two situations that matter most:
 *  damage concentrated in eighty residues of one interface, and damage spread evenly along
 *  two thousand. Those are different diseases, they imply different therapies, and their
 *  totals are identical.
 *
 *  STACKED BY SIGNIFICANCE, ON A COMMON BASELINE. Pathogenic below, uncertain above, so the
 *  pathogenic profile — the one a reader is actually asking about — sits on the axis where
 *  its shape can be read, and the uncertain mass sits on top of it where its *bulk* is
 *  obvious without competing for the baseline.
 *
 *  WHAT IT CANNOT SHOW, and the caller must print: variant density tracks sequencing depth
 *  and curation attention as well as biology. A spike is a hotspot OR a well-studied exon.
 */
export function NeedlePlot({
  series, span, bins, width = 900, height = 300, recurrent = [], lengthFrom,
  features = [], ariaLabel, readAloud, labels,
}: NeedlePlotProps) {
  const [hover, setHover] = useState<number | null>(null);

  const order = ["pathogenic", "conflicting", "uncertain", "benign"] as const;
  const TRACK_SWATCH = {
    domain: css.swDomain, membrane: css.swMembrane, motif: css.swMotif,
    active: css.swActive, binding: css.swBinding,
  } as const;
  const SWATCH = {
    pathogenic: css.swPathogenic, conflicting: css.swConflicting,
    uncertain: css.swUncertain, benign: css.swBenign,
  } as const;
  const present = order.filter((k) => series[k]?.some((v) => v > 0));

  const totals = useMemo(
    () => Array.from({ length: bins }, (_, i) =>
      present.reduce((s, k) => s + (series[k]?.[i] ?? 0), 0)),
    [series, bins, present],
  );
  const peak = Math.max(...totals, 1);
  const grand = totals.reduce((s, v) => s + v, 0);

  return (
    <div className={css.wrap}>
      {readAloud && (
        <ReadAloud form="Needle plot"
                   source="Standard in variant interpretation since cBioPortal / MutationMapper.">
          {readAloud}
        </ReadAloud>
      )}

      {/* The track needs 34px of its own under the axis line, and the axis needs its
          label under that. Reserving it in the margin rather than overlapping is why the
          backbone can sit exactly on the boundary. */}
      <PlotFrame width={width} height={height + (features.length ? 34 : 0)}
                 scrollAtWidth={640} ariaLabel={ariaLabel}
                 margin={{ top: 28, right: 24, bottom: features.length ? 86 : 52, left: 56 }}>
        {(box) => {
          const x = linear([1, span], [box.x0, box.x1]);
          const y = linear([0, peak], [box.y0, box.y1]);
          /* NEEDLES, NOT BARS. The first version sized the mark to fill its bin, which at
             60 bins across 1,000px is a 15px block — a histogram wearing a needle plot's
             name, and the whole point of the form is that POSITION is exact and height is
             secondary. Capped at 5px, so the marks stay separated by ground. */
          const binWidth = Math.min(5, Math.max(2, box.width / bins - 3));

          return (
            <>
              <AxisX scale={x} box={box} label={labels.axis} format={(v) => fmtInt(Math.round(v))}
                     ticks={6} note={lengthFrom} />

              {/* The protein itself: a bar the needles stand on. Without it the axis is an
                  abstraction; with it the reader is looking at a molecule. */}
              <rect x={box.x0} y={box.y0 - 6} width={box.width} height={6}
                    className={css.backbone} rx={3} />

              {/* THE PARTS OF THE MOLECULE, under the needles that fall on them.
                  Two rows: spans (domains, membrane passes, motifs) on the first, single
                  catalytic and binding residues as ticks on the second, because a 1-residue
                  feature drawn on the span row is invisible next to a 300-residue domain. */}
              {features.map((f, i) => {
                const wide = f.end - f.start > 0;
                const x0 = x(f.start);
                const x1 = Math.max(x0 + 2, x(f.end));
                const single = f.kind === "active" || f.kind === "binding";
                /* BELOW the axis label, not between the axis line and it. At +4 the track
                   sat exactly where AxisX prints its ticks, and the domain boxes covered
                   "500" and "1,000" — a track that hides the axis it is indexed against. */
                const top = box.y0 + (single ? 70 : 48);
                return (
                  <g key={`${f.kind}-${f.start}-${i}`}>
                    <rect x={x0} y={top} width={single && !wide ? 2.5 : x1 - x0}
                          height={single ? 10 : 14}
                          className={css[f.kind]} rx={single ? 1 : 2}>
                      <title>{`${f.label || f.kind} · ${f.start}–${f.end}`}</title>
                    </rect>
                    {/* A label only when the box can hold it. A clipped word is worse than
                        no word: the reader believes they read a name. */}
                    {!single && x1 - x0 > 58 && f.label && (
                      <text x={(x0 + x1) / 2} y={top + 11} textAnchor="middle"
                            className={css.featureLabel}>
                        {f.label.length > (x1 - x0) / 6
                          ? f.label.slice(0, Math.max(3, Math.floor((x1 - x0) / 6))) + "…"
                          : f.label}
                      </text>
                    )}
                  </g>
                );
              })}

              {Array.from({ length: bins }, (_, i) => {
                if (!totals[i]) return null;
                const cx = x(((i + 0.5) / bins) * span);
                let base = box.y0 - 6;
                return (
                  <g key={i}
                     onPointerEnter={() => setHover(i)}
                     onPointerLeave={() => setHover(null)}>
                    {/* The stem, drawn once to the full height: a stack of tiny rectangles
                        with no stem reads as a bar chart, and the point of a needle plot is
                        that position is exact and height is secondary. */}
                    <line x1={cx} x2={cx} y1={box.y0 - 6} y2={y(totals[i])}
                          className={css.stem} />
                    {present.map((k) => {
                      const v = series[k]?.[i] ?? 0;
                      if (!v) return null;
                      const h = box.y0 - 6 - y(v) + y(0) - y(0);
                      const top = base - (y(0) - y(v));
                      const rect = (
                        <rect key={k} x={cx - binWidth / 2} y={top}
                              width={binWidth} height={Math.max(1.5, y(0) - y(v))}
                              className={css[k]} rx={1} />
                      );
                      base = top;
                      void h;
                      return rect;
                    })}
                  </g>
                );
              })}

              {/* Recurrent residues, labelled. A residue hit two hundred times is a fact
                  about the gene and deserves its number printed, not a hover. */}
              {/* Overlapping labels are worse than fewer labels: two numbers printed on
                  top of each other read as one wrong number. Anything closer than 60px to
                  the previous marker is dropped. */}
              {recurrent
                .slice()
                .sort((a, b) => a.pos - b.pos)
                .filter((r, i, arr) => i === 0 || x(r.pos) - x(arr[i - 1].pos) > 60)
                .slice(0, 4)
                .map((r) => (
                <g key={r.pos}>
                  <line x1={x(r.pos)} x2={x(r.pos)} y1={box.y1} y2={box.y0 - 6}
                        className={css.marker} />
                  <text x={x(r.pos)} y={box.y1 - 8} textAnchor="middle" className={css.markerText}>
                    {r.pos} · {r.n}×
                  </text>
                </g>
              ))}
            </>
          );
        }}
      </PlotFrame>

      <div className={css.legend}>
        {present.map((k) => (
          <span key={k} className={css.legendItem}>
            <i className={`${css.swatch} ${SWATCH[k]}`} /> {labels[k]}
          </span>
        ))}
        <span className={css.legendCount}>{fmtInt(grand)} {labels.placed}</span>
      </div>

      {/* The track's own legend, separate from the variants'. They encode different things
          and one combined row would read as one scale. */}
      {features.length > 0 && (
        <div className={css.legend}>
          {(["domain", "membrane", "motif", "active", "binding"] as const)
            .filter((k) => features.some((f) => f.kind === k) && labels[k])
            .map((k) => (
              <span key={k} className={css.legendItem}>
                {/* TRACK_SWATCH, not the SVG class: an HTML span takes `background` and the
                    SVG rect takes `fill`. Using the drawing class on the legend is how the
                    variant legend came out colourless the first time. */}
                <i className={`${css.swatch} ${TRACK_SWATCH[k]}`} /> {labels[k]}
              </span>
            ))}
        </div>
      )}

      <p className={css.readout} role="status" aria-live="polite">
        {hover != null && totals[hover] > 0 && (
          <>
            {labels.residues} {fmtInt(Math.round((hover / bins) * span) + 1)}–
            {fmtInt(Math.round(((hover + 1) / bins) * span))}:{" "}
            {present.filter((k) => series[k]?.[hover]).map((k) =>
              `${fmtInt(series[k]![hover])} ${labels[k]}`).join(" · ")}
          </>
        )}
      </p>
    </div>
  );
}
