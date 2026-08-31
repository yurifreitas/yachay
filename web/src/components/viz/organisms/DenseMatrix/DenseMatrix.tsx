import { useEffect, useMemo, useRef, useState } from "react";
import { ReadAloud } from "../../atoms/ReadAloud";
import css from "./DenseMatrix.module.css";
import type { DenseMatrixProps } from "./DenseMatrix.types";

/** A quantised data matrix, drawn a byte at a time.
 *
 *  THE DIFFERENCE FROM `MatrixPlot`, which also draws a matrix on a canvas: that one takes an
 *  edge list and accumulates a density, because a graph is sparse and its matrix is mostly
 *  zeros. This takes a DENSE byte array where every cell is a measurement, and the value —
 *  not the count — is the ink. A CRISPR screen has no zeros to skip: every gene was tested in
 *  every line, and the flat majority is as much a finding as the lethal minority.
 *
 *  A DIVERGING RAMP, CENTRED ON NO EFFECT. Gene effect is signed: negative means the cells
 *  needed the gene, positive means losing it helped them. A sequential ramp would make "no
 *  effect" a colour partway along a scale and put the two directions on the same side of it,
 *  which for this data is the whole reading destroyed. Zero is the page's own background, so
 *  the flat majority disappears and only the effects carry ink.
 *
 *  THE ROW STRIP IS NOT DECORATION. Twelve hundred columns of dependency mean nothing without
 *  knowing which lines are which: a block is a lineage block only if the rows in it are the
 *  same tissue. The strip is the only thing that makes that checkable by eye.
 */
export function DenseMatrix({
  bytes, rows, cols, rowLabels, rowGroups, colLabels, colMargin, marginLabel,
  height = 620, ariaLabel, readAloud, source, orderings, ordering, onOrdering,
}: DenseMatrixProps) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  const [hover, setHover] = useState<{ r: number; c: number; v: number } | null>(null);

  // A colour per distinct group, assigned by first appearance so the strip is stable across
  // orderings. Hue-spread rather than a named palette: there are more lineages than any
  // categorical palette holds, and the strip is for grouping, not for identification.
  const groupColour = useMemo(() => {
    const seen = new Map<string, string>();
    let i = 0;
    for (const g of rowGroups ?? []) {
      if (!seen.has(g)) {
        seen.set(g, `oklch(64% 0.14 ${(i * 47) % 360})`);
        i++;
      }
    }
    return seen;
  }, [rowGroups]);

  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = cols * dpr;
    cv.height = rows * dpr;
    const ctx = cv.getContext("2d", { alpha: false });
    if (!ctx) return;

    const style = getComputedStyle(cv);
    const bg = rgb(style.getPropertyValue("--dm-bg") || "#ffffff");
    const neg = rgb(style.getPropertyValue("--dm-neg") || "#1b4965");
    const pos = rgb(style.getPropertyValue("--dm-pos") || "#a3320b");

    const img = ctx.createImageData(cols, rows);
    // The byte encodes the clipped range; the caller says where zero sits inside it.
    const zero = 255 * ((0 - (orderings?.lo ?? -2)) / ((orderings?.hi ?? 1) - (orderings?.lo ?? -2)));
    for (let i = 0; i < bytes.length; i++) {
      const v = bytes[i];
      // Distance from no-effect, as a fraction of the arm it falls on.
      //
      // The exponent is a display choice and it is a real one: 0.5 (a square root) lifts a
      // 10% deviation to 32% ink, which on a matrix whose values cluster hard near zero
      // renders almost everything saturated. 0.75 keeps weak effects visible without
      // claiming they are strong, and the flat majority stays as the page's own background —
      // which is the single most important thing this figure has to show.
      const t = Math.pow(
        Math.min(1, Math.abs(v - zero) / (v < zero ? zero : 255 - zero)), 0.75);
      const c = v < zero ? neg : pos;
      const o = i * 4;
      img.data[o] = bg.r + (c.r - bg.r) * t;
      img.data[o + 1] = bg.g + (c.g - bg.g) * t;
      img.data[o + 2] = bg.b + (c.b - bg.b) * t;
      img.data[o + 3] = 255;
    }
    // Drawn at native size into an offscreen bitmap, then scaled by CSS. Scaling the
    // ImageData directly would smooth it, and a smoothed dependency matrix invents
    // intermediate values between two genes that were never measured together.
    const off = document.createElement("canvas");
    off.width = cols;
    off.height = rows;
    off.getContext("2d")!.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(off, 0, 0, cv.width, cv.height);
  }, [bytes, rows, cols, orderings]);

  return (
    <div className={css.wrap}>
      {orderings && onOrdering && (
        <div className={css.controls} role="group" aria-label="Ordering">
          {Object.keys(orderings.options).map((k) => (
            <button key={k} onClick={() => onOrdering(k)}
                    className={k === ordering ? css.tabOn : css.tab}>
              {k}
            </button>
          ))}
          <span className={css.orderNote}>{orderings.options[ordering ?? ""]?.says}</span>
        </div>
      )}

      <div className={css.stage} style={{ height }}>
        {/* The lineage strip, one band per row, in the current row order. */}
        {rowGroups && (
          <div className={css.strip} aria-hidden="true">
            {rowGroups.map((g, i) => (
              <span key={i} style={{ background: groupColour.get(g) }} title={g} />
            ))}
          </div>
        )}
        <canvas
          ref={ref}
          className={css.canvas}
          role="img"
          aria-label={ariaLabel}
          onMouseMove={(ev) => {
            const el = ev.target as HTMLCanvasElement;
            const b = el.getBoundingClientRect();
            const c = Math.floor(((ev.clientX - b.left) / b.width) * cols);
            const r = Math.floor(((ev.clientY - b.top) / b.height) * rows);
            if (r >= 0 && r < rows && c >= 0 && c < cols) {
              setHover({ r, c, v: bytes[r * cols + c] });
            }
          }}
          onMouseLeave={() => setHover(null)}
        />
      </div>

      {/* The essential-share margin, under the columns it describes. */}
      {colMargin && (
        <div className={css.margin} aria-hidden="true">
          {colMargin.map((v, i) => (
            <span key={i} style={{ opacity: 0.08 + 0.92 * v }} />
          ))}
        </div>
      )}
      {colMargin && <p className={css.marginLabel}>{marginLabel}</p>}

      <p className={css.hint}>
        {hover
          ? <>
              <strong>{rowLabels?.[hover.r] ?? `row ${hover.r}`}</strong>
              {rowGroups?.[hover.r] ? ` · ${rowGroups[hover.r]}` : ""}
              {" — "}
              <strong>{colLabels?.[hover.c] || `bin ${hover.c}`}</strong>
              {" · "}
              {fmtValue(hover.v, orderings?.lo ?? -2, orderings?.hi ?? 1)}
            </>
          : source}
      </p>

      <ReadAloud form="dense matrix" source={source}>{readAloud}</ReadAloud>
    </div>
  );
}

function fmtValue(byte: number, lo: number, hi: number): string {
  const v = lo + (byte / 255) * (hi - lo);
  return `${v.toFixed(2)} gene effect`;
}

function rgb(h: string) {
  const s = h.replace("#", "").trim();
  const full = s.length === 3 ? s.split("").map((c) => c + c).join("") : s;
  const v = parseInt(full || "ffffff", 16);
  return { r: (v >> 16) & 255, g: (v >> 8) & 255, b: v & 255 };
}
