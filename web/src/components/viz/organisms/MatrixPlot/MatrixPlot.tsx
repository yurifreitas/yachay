import { useEffect, useMemo, useRef, useState } from "react";
import { ReadAloud } from "../../atoms/ReadAloud";
import ChoiceGroup from "../../../atoms/ChoiceGroup";
import css from "./MatrixPlot.module.css";
import type { MatrixPlotProps } from "./MatrixPlot.types";

/** A graph as a reordered adjacency matrix, on a canvas.
 *
 *  THE FORM is Bertin's reorderable matrix (1967), and the reason to reach for it over a
 *  node-link drawing is not taste. A force-directed layout of 38,746 edges is a hairball: at
 *  this density the picture is dominated by the repulsion constant, two runs of the same
 *  layout look different, and no distance in it can be read. A matrix draws every edge exactly
 *  once at a fixed position with no parameter to tune. Communities appear as blocks on the
 *  diagonal, and the edges BETWEEN communities — the ones a hairball buries in its centre —
 *  appear as off-diagonal texture.
 *
 *  WHY CANVAS. 3,335 x 3,335 is 11.1 million cells. As DOM that is not slow, it is impossible.
 *  Here it is one typed-array pass per redraw, at a few milliseconds, so switching the
 *  ordering is instant — which matters, because the comparison BETWEEN orderings is the whole
 *  argument and it only works if the reader can flip back and forth without losing the image.
 *
 *  THE ORDERING IS THE ARGUMENT (ADR 0008). Every ordering is computed in Python and shipped;
 *  this component only draws. `consensus` was told where the communities are. `spectral` was
 *  not. If the blocks survive the switch they are in the graph; if they only appear in the
 *  ordering that assumed them, they are not. `degree` is the control.
 *
 *  ANTI-ALIASING IS DELIBERATELY OFF. At 3,335 genes in about 700 pixels each cell is a fifth
 *  of a pixel, so several gene pairs share one. Painting them with alpha accumulation would
 *  make a dense block look darker than a sparse one — which is correct and is exactly what is
 *  wanted here: the shade IS the local edge density, and it is stated in the caption rather
 *  than left for the reader to infer.
 */
export function MatrixPlot({
  n, edges, orderings, blocks = [], confidence, size = 760, ariaLabel, readAloud, source,
  labelFor,
}: MatrixPlotProps) {
  const keys = Object.keys(orderings);
  const [which, setWhich] = useState(keys[0]);
  const [hover, setHover] = useState<{ i: number; j: number } | null>(null);
  const ref = useRef<HTMLCanvasElement | null>(null);

  // Position of each gene under the current ordering: rank[gene] = where it sits. The shipped
  // array is the inverse (which gene sits at each slot), so this is inverted once per switch
  // rather than once per edge.
  const rank = useMemo(() => {
    const order = orderings[which].index;
    const out = new Int32Array(n);
    for (let s = 0; s < n; s++) out[order[s]] = s;
    return out;
  }, [orderings, which, n]);

  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = size * dpr;
    cv.height = size * dpr;
    const ctx = cv.getContext("2d", { alpha: false });
    if (!ctx) return;

    const style = getComputedStyle(cv);
    ctx.fillStyle = style.getPropertyValue("--matrix-bg") || "#fff";
    ctx.fillRect(0, 0, cv.width, cv.height);

    // Density accumulated into a pixel grid first, then painted once. Painting per edge
    // would make the result depend on draw order at the sub-pixel scale.
    const px = Math.floor(size * dpr);
    const grid = new Float32Array(px * px);
    const scale = px / n;
    for (let e = 0; e < edges.i.length; e++) {
      const a = rank[edges.i[e]];
      const b = rank[edges.j[e]];
      const x = Math.floor(a * scale);
      const y = Math.floor(b * scale);
      grid[y * px + x] += 1;
      grid[x * px + y] += 1;              // symmetric: the matrix is undirected
    }

    let peak = 0;
    for (let k = 0; k < grid.length; k++) if (grid[k] > peak) peak = grid[k];

    const ink = (style.getPropertyValue("--matrix-ink") || "#1b1f27").trim();
    const img = ctx.createImageData(px, px);
    const bg = hexToRgb(style.getPropertyValue("--matrix-bg").trim() || "#ffffff");
    const fg = hexToRgb(ink);
    for (let k = 0; k < grid.length; k++) {
      // Square-root, not linear: a handful of pixels carry twenty pairs and the rest carry
      // one, so a linear ramp renders the whole matrix as near-white with four black dots.
      const t = peak ? Math.sqrt(grid[k] / peak) : 0;
      const o = k * 4;
      img.data[o] = bg.r + (fg.r - bg.r) * t;
      img.data[o + 1] = bg.g + (fg.g - bg.g) * t;
      img.data[o + 2] = bg.b + (fg.b - bg.b) * t;
      img.data[o + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);

    // Community rules, only under the ordering that claims them. Drawing them over `spectral`
    // would hand the reader the answer to the question the switch is asking.
    if (which === keys[0] && blocks.length) {
      ctx.strokeStyle = (style.getPropertyValue("--matrix-rule") || "#d33").trim();
      ctx.lineWidth = Math.max(1, dpr * 0.5);
      ctx.globalAlpha = 0.5;
      for (const [start, end] of blocks) {
        if (end - start < 12) continue;      // rules for blocks too small to see are noise
        const a = (start / n) * px;
        const b = (end / n) * px;
        ctx.strokeRect(a, a, b - a, b - a);
      }
      ctx.globalAlpha = 1;
    }
  }, [rank, edges, n, size, blocks, which, keys]);

  return (
    <div className={css.wrap}>
      <ChoiceGroup
        label="Ordering"
        value={which}
        onChange={setWhich}
        choices={keys.map((k) => ({ id: k, label: k }))}
      />

      <div className={css.stage} style={{ width: size }}>
        <canvas
          ref={ref}
          className={css.canvas}
          style={{ width: size, height: size }}
          role="img"
          aria-label={ariaLabel}
          onMouseMove={(ev) => {
            const r = (ev.target as HTMLCanvasElement).getBoundingClientRect();
            const i = Math.floor(((ev.clientX - r.left) / r.width) * n);
            const j = Math.floor(((ev.clientY - r.top) / r.height) * n);
            setHover(i >= 0 && i < n && j >= 0 && j < n ? { i, j } : null);
          }}
          onMouseLeave={() => setHover(null)}
        />

        {/* The confidence margin. Each gene's consensus confidence as a strip beside its own
            row, so "this block is firm" and "this block is an artefact of the seed" are the
            same glance rather than two screens. */}
        {confidence && (
          <div className={css.margin} style={{ height: size }}>
            {Array.from({ length: 120 }, (_, b) => {
              const from = Math.floor((b / 120) * n);
              const to = Math.floor(((b + 1) / 120) * n);
              let sum = 0;
              let cnt = 0;
              for (let s = from; s < to; s++) {
                const c = confidence[orderings[which].index[s]];
                if (c >= 0) { sum += c; cnt++; }
              }
              const v = cnt ? sum / cnt : -1;
              return (
                <span
                  key={b}
                  className={css.marginCell}
                  style={{ opacity: v < 0 ? 0.08 : 0.15 + 0.85 * v }}
                  title={v < 0 ? "no confidence" : v.toFixed(2)}
                />
              );
            })}
          </div>
        )}
      </div>

      <p className={css.hint}>
        {hover && labelFor
          ? <>row <strong>{labelFor(orderings[which].index[hover.j])}</strong> · column{" "}
             <strong>{labelFor(orderings[which].index[hover.i])}</strong></>
          : orderings[which].says}
      </p>

      <ReadAloud form="reordered adjacency matrix" source={source}>{readAloud}</ReadAloud>
    </div>
  );
}

function hexToRgb(h: string) {
  const s = h.replace("#", "").trim();
  const full = s.length === 3 ? s.split("").map((c) => c + c).join("") : s;
  const v = parseInt(full || "ffffff", 16);
  return { r: (v >> 16) & 255, g: (v >> 8) & 255, b: v & 255 };
}
