/** Dense scatter on a canvas, with SVG kept for the axes and annotation.
 *
 * WHY NOT SVG. One <circle> per point costs a DOM node, a style resolution and a layout
 * box. At 17,916 points that is ~18k nodes: the first paint takes hundreds of
 * milliseconds, every hover re-runs style matching over the whole tree, and a filter
 * toggle rebuilds the lot. A canvas draws the same points as pixels in one pass with no
 * DOM at all, and redraws in a couple of milliseconds.
 *
 * WHAT YOU LOSE, and how each is bought back here:
 *   - hover targets       -> a uniform grid index (below), which is O(1) per pointer move
 *   - crisp on retina     -> the canvas is sized in device pixels and scaled back by CSS
 *   - text and axes       -> left in SVG on top, where they stay selectable and legible
 *   - "it's in the DOM"   -> a table view alongside, which the accessibility pass needs
 *                            anyway
 *
 * The layered arrangement — canvas for marks, SVG for everything else — is the standard
 * answer once a chart passes a few thousand marks, and it keeps the axis code shared with
 * every other chart here.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import type { Scale } from "../lib/scale";

export interface PointSet {
  n: Float32Array;
  score: Float32Array;
  z: Float32Array;
  cls: Uint8Array;
  names: string[];
  total: number;
  shown: number;
  sampleRate: number;
}

/** Decode the columnar payload once per run, not per render. */
export function decodePoints(raw: {
  n: string; score: string; z: string; cls: string; names: string;
  total: number; shown: number; sampleRate: number;
}): PointSet {
  const f32 = (b64: string) => {
    const bin = atob(b64);
    const buf = new ArrayBuffer(bin.length);
    const view = new Uint8Array(buf);
    for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i);
    return new Float32Array(buf);
  };
  const u8 = (b64: string) => {
    const bin = atob(b64);
    const view = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i);
    return view;
  };
  return {
    n: f32(raw.n),
    score: f32(raw.score),
    z: f32(raw.z),
    cls: u8(raw.cls),
    names: raw.names.split("\n"),
    total: raw.total,
    shown: raw.shown,
    sampleRate: raw.sampleRate,
  };
}

/** Repaint trigger: canvas has no cascade, so a theme change must be observed. */
function useThemeTick() {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const bump = () => setTick((t) => t + 1);
    const mo = new MutationObserver(bump);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", bump);
    return () => { mo.disconnect(); mq.removeEventListener("change", bump); };
  }, []);
  return tick;
}

/** Uniform-grid spatial index: the cheap half of a quadtree, and enough here.
 *
 *  Points are bucketed by pixel position once. A pointer move reads its own cell and the
 *  eight around it, so the search is bounded by local density rather than by the total
 *  point count — which is the property that matters when the count grows.
 */
class HitIndex {
  private cells = new Map<number, number[]>();
  constructor(private size: number, private cols: number) {}
  key(px: number, py: number) {
    return ((py / this.size) | 0) * this.cols + ((px / this.size) | 0);
  }
  add(px: number, py: number, i: number) {
    const k = this.key(px, py);
    const c = this.cells.get(k);
    if (c) c.push(i);
    else this.cells.set(k, [i]);
  }
  near(px: number, py: number): number[] {
    const out: number[] = [];
    const cx = (px / this.size) | 0;
    const cy = (py / this.size) | 0;
    for (let dy = -1; dy <= 1; dy++)
      for (let dx = -1; dx <= 1; dx++) {
        const c = this.cells.get((cy + dy) * this.cols + (cx + dx));
        if (c) out.push(...c);
      }
    return out;
  }
}

export interface ScatterProps {
  pts: PointSet;
  x: Scale;
  y: Scale;
  /** Which value feeds the y scale. */
  yOf: (pts: PointSet, i: number) => number;
  width: number;
  height: number;
  /** Class colours, indexed by `cls`. Slot 0 is the recessive bulk. */
  colors: [string, string, string];
  /** Only draw points matching this, keeping the index intact. */
  filter?: (pts: PointSet, i: number) => boolean;
  onHover?: (i: number | null, ev?: { clientX: number; clientY: number }) => void;
}

export default function CanvasScatter({
  pts, x, y, yOf, width, height, colors, filter, onHover,
}: ScatterProps) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  // Canvas pixels do not restyle themselves when the theme token changes, the way an
  // SVG fill would. Watch the root attribute and the OS setting, and repaint.
  const theme = useThemeTick();

  // Pixel positions are computed once per (scale, data) pair and reused by both the
  // painter and the hit index — the projection is the expensive part, not the drawing.
  const proj = useMemo(() => {
    const m = pts.n.length;
    const px = new Float32Array(m);
    const py = new Float32Array(m);
    for (let i = 0; i < m; i++) {
      px[i] = x(pts.n[i]);
      py[i] = y(yOf(pts, i));
    }
    const index = new HitIndex(12, Math.ceil(width / 12) + 2);
    for (let i = 0; i < m; i++) {
      if (Number.isFinite(px[i]) && Number.isFinite(py[i])) index.add(px[i], py[i], i);
    }
    return { px, py, index };
  }, [pts, x, y, yOf, width]);

  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    // Device pixels, not CSS pixels: a 1px dot drawn on an unscaled canvas is a blurry
    // 2x2 smear on a retina display.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = width * dpr;
    cv.height = height * dpr;
    const ctx = cv.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    // Canvas does NOT resolve CSS custom properties: `ctx.fillStyle = "var(--x)"` is an
    // invalid value, silently ignored, leaving whatever colour was set before — which
    // renders every point in the default black and looks like a data problem rather than
    // a drawing one. Resolve the tokens against the live element instead, so the theme
    // still drives the palette.
    const css = getComputedStyle(cv);
    const resolve = (c: string) => {
      const m = /^var\((--[\w-]+)\)$/.exec(c.trim());
      return m ? css.getPropertyValue(m[1]).trim() || "#888" : c;
    };
    const paint = colors.map(resolve) as [string, string, string];

    // Two passes so the marked classes are never buried under the bulk. Within a pass
    // the order is data order, which is stable between renders.
    const { px, py } = proj;
    for (const pass of [0, 1]) {
      for (let i = 0; i < pts.n.length; i++) {
        const c = pts.cls[i];
        if ((pass === 0) !== (c === 0)) continue;
        if (filter && !filter(pts, i)) continue;
        ctx.fillStyle = paint[c];
        // The bulk is drawn semi-transparent so overlap reads as density rather than as a
        // solid blob -- the only honest way to show 10k points in 880px.
        ctx.globalAlpha = c === 0 ? 0.38 : 0.85;
        const r = c === 0 ? 1.6 : 2.6;
        ctx.beginPath();
        ctx.arc(px[i], py[i], r, 0, 6.283185307179586);
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
  }, [proj, pts, width, height, colors, filter, theme]);

  return (
    <canvas
      ref={ref}
      style={{ width, height, position: "absolute", left: 0, top: 0 }}
      onMouseMove={(e) => {
        if (!onHover) return;
        const r = e.currentTarget.getBoundingClientRect();
        const mx = e.clientX - r.left;
        const my = e.clientY - r.top;
        let best = -1;
        let bestD = 64; // 8px radius, squared
        for (const i of proj.index.near(mx, my)) {
          if (filter && !filter(pts, i)) continue;
          const dx = proj.px[i] - mx;
          const dy = proj.py[i] - my;
          const d = dx * dx + dy * dy;
          if (d < bestD) { bestD = d; best = i; }
        }
        onHover(best >= 0 ? best : null, e);
      }}
      onMouseLeave={() => onHover?.(null)}
    />
  );
}
