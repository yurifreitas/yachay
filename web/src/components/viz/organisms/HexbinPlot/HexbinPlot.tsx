import { useMemo, useState } from "react";
import { PlotFrame, PlotClip, type PlotBox } from "../../atoms/PlotFrame";
import { AxisX, AxisY } from "../../atoms/Axis";
import { ReadAloud } from "../../atoms/ReadAloud";
import { hexbin, hexPath, type HexBin } from "../../../../lib/viz/density";
import type { Scale } from "../../../../lib/scale";
import css from "./HexbinPlot.module.css";
import type { HexbinPlotProps } from "./HexbinPlot.types";

/** A dense cloud drawn as DENSITY, with the sparse corner drawn as points.
 *
 *  THE PROBLEM THIS FORM SOLVES. A scatter of ten thousand marks is not a scatter plot; it
 *  is a silhouette. Overlapping alpha is the usual patch and it fails in both directions —
 *  at low alpha the sparse points vanish, at high alpha the core saturates and every count
 *  above the saturation point looks identical. Neither tells you whether the middle holds
 *  fifty points or five thousand.
 *
 *  Hexagonal binning (Carr et al., 1987) answers the density question exactly: each cell
 *  states its count, on a sequential ramp, and hexagons avoid the axis-aligned banding that
 *  square bins produce. What it cannot do is show an individual — and in a screen, the
 *  individual in the sparse corner IS the finding.
 *
 *  So this is a HYBRID, which is the standard resolution and the one this repository needs:
 *  cells above `pointThreshold` are drawn as density, cells at or below it give their points
 *  back as marks. The dense bulk becomes legible without the interesting tail being averaged
 *  away, and the boundary is a stated number rather than an alpha value nobody can read off.
 */
export function HexbinPlot({
  xs, ys, x: xOf, y: yOf, width = 860, height = 440, radius = 7, pointThreshold = 3,
  xLabel, yLabel, xNote, yNote, xFormat, yFormat, ariaLabel, readAloud,
  colorOf, labelOf, keep, annotations, id,
}: HexbinPlotProps) {
  const [hover, setHover] = useState<{ bin: HexBin; cx: number; cy: number } | null>(null);

  const margin = { top: 18, right: 24, bottom: 52, left: 66 };

  return (
    <div className={css.wrap}>
      {readAloud && (
        <ReadAloud form="Hexbin + points" source="Carr, Littlefield, Nicholson & Littlefield (1987), JASA.">
          {readAloud}
        </ReadAloud>
      )}

      <PlotFrame width={width} height={height} margin={margin} ariaLabel={ariaLabel}
                 scrollAtWidth={620}>
        {(box) => {
          const x = xOf([box.x0, box.x1]);
          const y = yOf([box.y0, box.y1]);
          return (
          <HexbinMarks
            box={box} xs={xs} ys={ys} x={x} y={y} radius={radius}
            pointThreshold={pointThreshold} keep={keep} colorOf={colorOf} id={id}
            onHover={setHover}
            axes={
              <>
                <AxisY scale={y} box={box} label={yLabel} note={yNote}
                       format={yFormat} grid />
                <AxisX scale={x} box={box} label={xLabel} note={xNote} format={xFormat} />
              </>
            }
            annotations={annotations?.(box, x, y)}
          />
          );
        }}
      </PlotFrame>

      {/* The count legend is a ramp with its own numbers, not a gradient bar with two ends.
          A reader has to be able to say "that cell is about forty genes". */}
      <div className={css.foot}>
        <span className={css.legendTitle}>entities per cell</span>
        <span className={css.ramp} aria-hidden="true">
          {[0.15, 0.35, 0.55, 0.75, 1].map((t) => (
            <i key={t} style={{ background: `color-mix(in oklab, var(--seq-650) ${t * 100}%, var(--seq-200))` }} />
          ))}
        </span>
        <span className={css.legendNote}>
          cells holding {pointThreshold} or fewer are drawn as individual marks
        </span>
      </div>

      {hover && (
        <p className={css.readout} role="status" aria-live="polite">
          <strong>{hover.bin.count}</strong>{" "}
          {hover.bin.count === 1 ? "entity" : "entities"} in this cell
          {labelOf && hover.bin.count <= 6 && (
            <span className={css.names}>
              {" — "}{hover.bin.indices.map(labelOf).join(", ")}
            </span>
          )}
        </p>
      )}
    </div>
  );
}

/** The marks themselves, separated so the binning memo depends on the box and nothing else.
 *  Binning happens in SCREEN space — see `hexbin` — which is why it cannot be hoisted above
 *  the frame that decides how big the screen space is. */
function HexbinMarks({
  box, xs, ys, x, y, radius, pointThreshold, keep, colorOf, axes, annotations, onHover, id,
}: {
  box: PlotBox; xs: ArrayLike<number>; ys: ArrayLike<number>; x: Scale; y: Scale;
  radius: number; pointThreshold: number; keep?: (i: number) => boolean;
  colorOf?: (i: number) => string; axes: React.ReactNode; annotations?: React.ReactNode;
  onHover: (h: { bin: HexBin; cx: number; cy: number } | null) => void; id: string;
}) {
  const bins = useMemo(() => {
    const px = new Float64Array(xs.length);
    const py = new Float64Array(xs.length);
    for (let i = 0; i < xs.length; i++) { px[i] = x(xs[i]); py[i] = y(ys[i]); }
    return hexbin(px, py, radius, keep);
  }, [xs, ys, x, y, radius, keep]);

  const max = bins.length ? bins[bins.length - 1].count : 1;
  const path = hexPath(radius);

  const dense = bins.filter((b) => b.count > pointThreshold);
  const sparse = bins.filter((b) => b.count <= pointThreshold);

  return (
    <>
      {axes}
      <PlotClip id={`hex-${id}`} box={box}>
        {/* Dense first, sparse over it: the individual mark is the thing being looked for,
            so nothing may cover it. */}
        {dense.map((b) => (
          <path
            key={`${b.x},${b.y}`}
            d={path}
            transform={`translate(${b.x},${b.y})`}
            className={css.hex}
            style={{
              // Perceptual mix along the sequential ramp. Count is ORDERED, so the encoding
              // is one hue getting darker — never a rainbow, which asks the reader to
              // remember an arbitrary order.
              fill: `color-mix(in oklab, var(--seq-650) ${(0.15 + 0.85 * (b.count / max)) * 100}%, var(--seq-200))`,
            }}
            onPointerEnter={() => onHover({ bin: b, cx: b.x, cy: b.y })}
            onPointerLeave={() => onHover(null)}
          >
            <title>{`${b.count} entities`}</title>
          </path>
        ))}
        {sparse.map((b) =>
          b.indices.map((i) => (
            <circle
              key={i}
              cx={x(xs[i])}
              cy={y(ys[i])}
              r={2.6}
              className={css.point}
              style={colorOf ? { fill: colorOf(i) } : undefined}
              onPointerEnter={() => onHover({ bin: b, cx: b.x, cy: b.y })}
              onPointerLeave={() => onHover(null)}
            />
          )),
        )}
      </PlotClip>
      {annotations}
    </>
  );
}
