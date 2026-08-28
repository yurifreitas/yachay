/** A thin ECharts host. One chart library in the app, per the standard — not three.
 *
 *  Why a wrapper at all: ECharts is imperative and lives outside React's tree, so three
 *  things have to be handled once rather than in every chart —
 *
 *    1. DISPOSAL. An undisposed instance leaks its canvas and its resize listener.
 *    2. RESIZE. ECharts does not observe its container; a ResizeObserver does.
 *    3. THEME. Charts take literal colours, so a theme change is not a restyle — the
 *       option has to be rebuilt. The builder is a function of the mode for that reason.
 *
 *  `build` receives the resolved mode and returns an option object. Keeping it a function
 *  rather than an object is what makes the theme swap correct by construction.
 */
import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import {
  CustomChart, ScatterChart, LineChart, BarChart, HeatmapChart, SankeyChart, GraphChart,
} from "echarts/charts";
import {
  GridComponent, TooltipComponent, LegendComponent, DataZoomComponent,
  VisualMapComponent, MarkLineComponent, TitleComponent, GraphicComponent,
} from "echarts/components";
import { resolveMode, type Mode } from "../../../lib/palette";

echarts.use([
  CanvasRenderer,
  CustomChart, ScatterChart, LineChart, BarChart, HeatmapChart, SankeyChart, GraphChart,
  GridComponent, TooltipComponent, LegendComponent, DataZoomComponent,
  VisualMapComponent, MarkLineComponent, TitleComponent, GraphicComponent,
]);

export type EChartProps = {
  /** Rebuilt whenever the theme changes, because colours are literals here. */
  build: (mode: Mode) => echarts.EChartsCoreOption;
  height: number;
  /** Spoken aloud in one sentence — every unfamiliar form owes the reader this. */
  ariaLabel: string;
  /** Extra dependencies that should trigger a rebuild. */
  deps?: unknown[];
};

export function EChart({ build, height, ariaLabel, deps = [] }: EChartProps) {
  const host = useRef<HTMLDivElement | null>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const [mode, setMode] = useState<Mode>(() =>
    typeof document === "undefined" ? "light" : resolveMode()
  );

  // The theme has three states, and only two of them stamp an attribute — so both the
  // stamp and the OS setting have to be watched.
  useEffect(() => {
    const sync = () => setMode(resolveMode());
    const mo = new MutationObserver(sync);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", sync);
    return () => {
      mo.disconnect();
      mq.removeEventListener("change", sync);
    };
  }, []);

  useEffect(() => {
    if (!host.current) return;
    chart.current ??= echarts.init(host.current, undefined, { renderer: "canvas" });
    chart.current.setOption(build(mode), true);
    // Measure again on the next frame. A ResizeObserver reacts to a box changing, but a
    // chart mounted (or re-optioned) mid-layout can be sized against a box that is about
    // to change — the symptom is a canvas wider than its column until something else
    // forces a resize. One frame later the layout has settled.
    const frame = requestAnimationFrame(() => chart.current?.resize());
    const ro = new ResizeObserver(() => chart.current?.resize());
    ro.observe(host.current);
    return () => { cancelAnimationFrame(frame); ro.disconnect(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, ...deps]);

  useEffect(() => () => { chart.current?.dispose(); chart.current = null; }, []);

  return <div ref={host} style={{ width: "100%", height }} role="img" aria-label={ariaLabel} />;
}
