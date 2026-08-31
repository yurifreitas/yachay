import { useEffect, useRef } from "react";
import { ReadAloud } from "../../atoms/ReadAloud";
import css from "./ScatterPair.module.css";
import type { ScatterPairProps } from "./ScatterPair.types";

/** The same points, twice, on a canvas — small multiples of one projection.
 *
 *  THE ARGUMENT THIS FORM MAKES. A number saying "the neighbour overlap between two runs is
 *  0.63" is a number a reader accepts and forgets. Two maps of the same 8,890 genes, from the
 *  same algorithm on the same data with nothing changed but the random seed, make the same
 *  point in a glance and cannot be waved away. Small multiples with a locked scale is the form
 *  for "these should be identical, and are not".
 *
 *  BOTH PANELS SHARE A DOMAIN, computed over both sets of points at once. Fitting each to its
 *  own extent would rescale them independently and hide exactly the difference the figure
 *  exists to show — the standard failure of side-by-side plots, and the reason the scale is
 *  computed here rather than per panel.
 *
 *  CANVAS, because 8,890 points twice is 17,780 DOM nodes for a figure whose whole content is
 *  where the ink is dense. Colour carries the cluster the practitioner would have believed.
 */
export function ScatterPair({
  a, b, labels, cluster, palette, width = 880, height = 400, ariaLabel, readAloud, source,
}: ScatterPairProps) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = width * dpr;
    cv.height = height * dpr;
    const ctx = cv.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const pad = 18;
    const panelW = (width - pad * 3) / 2;
    const panelH = height - pad * 2 - 18;

    // ONE DOMAIN FOR BOTH. See the note above: independent scales would hide the finding.
    const xs = [...a.x, ...b.x];
    const ys = [...a.y, ...b.y];
    const x0 = Math.min(...xs);
    const x1 = Math.max(...xs);
    const y0 = Math.min(...ys);
    const y1 = Math.max(...ys);
    const sx = (v: number, off: number) => off + ((v - x0) / (x1 - x0 || 1)) * panelW;
    const sy = (v: number) => pad + 18 + panelH - ((v - y0) / (y1 - y0 || 1)) * panelH;

    const style = getComputedStyle(cv);
    const colours = palette.map((p) => style.getPropertyValue(p).trim() || "#888");

    for (const [set, off, label] of [[a, pad, labels[0]], [b, pad * 2 + panelW, labels[1]]] as const) {
      ctx.fillStyle = style.getPropertyValue("--r-text-3").trim() || "#888";
      ctx.font = "11px system-ui, sans-serif";
      ctx.fillText(label, off, pad + 6);

      for (let i = 0; i < set.x.length; i++) {
        const c = cluster ? cluster[i] : 0;
        ctx.fillStyle = c < 0
          ? (style.getPropertyValue("--r-border-hi").trim() || "#ccc")
          : colours[c % colours.length];
        ctx.globalAlpha = 0.5;
        ctx.beginPath();
        ctx.arc(sx(set.x[i], off), sy(set.y[i]), 1.3, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }
  }, [a, b, labels, cluster, palette, width, height]);

  return (
    <div className={css.wrap}>
      <canvas ref={ref} className={css.canvas} role="img" aria-label={ariaLabel}
              style={{ width, height, maxWidth: "100%" }} />
      <ReadAloud form="small multiples, shared scale" source={source}>{readAloud}</ReadAloud>
    </div>
  );
}
