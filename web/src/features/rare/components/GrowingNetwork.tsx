/** A network that grows, instead of a diagram that does not.
 *
 *  WHAT WAS WRONG. The lupus graph on this site was hand-built, fixed at a couple of dozen
 *  nodes, and identical on every load. It illustrated a network; it was not one. The thesis's
 *  own phrasing for what it should be is G(t) — a graph whose nodes and edges change — and a
 *  picture cannot be that.
 *
 *  WHAT THIS IS. The real gene-gene graph: 5,524 genes, adjacent when they cause a common
 *  disease, shipped as a CSR adjacency rather than as coordinates. You pick a seed, the
 *  neighbourhood opens, and every click on a node expands the frontier from there. The graph
 *  is assembled in the browser and is different every time because the reader built it.
 *
 *  THE COLOUR IS A COMPUTATION, NOT A CATEGORY. Random walk with restart from the current
 *  seeds, run to convergence over whatever subgraph is open, recomputed on every expansion.
 *  That is network propagation — the operation the thesis names at the interactome rung — and
 *  it is the same x <- alpha*A*x + (1-alpha)*s iteration, done on the visible frontier.
 *
 *  WHY THE LAYOUT IS DETERMINISTIC. A force simulation would move the whole graph every time
 *  a node is added, so nothing could be compared between two states. Nodes are placed by
 *  propagation rank on a radial layout instead: distance from the centre means diffusion
 *  score, and a node keeps its place when its neighbours arrive.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRemoteData, DATA_URL } from "../../../lib/useRemoteData";
import type { GeneNetwork } from "../geneNetworkModel";
import css from "./GrowingNetwork.module.css";

const ALPHA = 0.6;          // restart probability's complement
const ITERATIONS = 40;      // ample for a few hundred visible nodes
const MAX_NODES = 320;      // beyond this the picture stops being readable, not the maths

type Placed = { id: number; x: number; y: number; score: number; r: number };

/** The graph is fetched, not imported: 632 kB of adjacency parsed before first paint is the
 *  wrong trade when it is needed to fill one panel and not to draw the page. The four states
 *  below are all real — an asset can 404 after a bad deploy, and a spinner that never resolves
 *  is the worst of them to ship. */
export function GrowingNetwork() {
  const remote = useRemoteData<GeneNetwork>(DATA_URL("gene_network"));
  if (remote.state === "loading") {
    return (
      <div className={css.pending} role="status" aria-live="polite">
        <span className={css.pendingBar} />
        <span>Loading the adjacency — 5,524 genes, fetched rather than bundled.</span>
      </div>
    );
  }
  if (remote.state === "error") {
    return (
      <div className={css.failed} role="alert">
        <strong>The graph did not load.</strong> {remote.message}. It is written to{" "}
        <code>public/data/gene_network.json</code> by <code>npm run data</code>; if that file is
        missing the build did not run, and this panel says so rather than rendering an empty
        canvas.
      </div>
    );
  }
  return <Network g={remote.data} />;
}

function Network({ g }: { g: GeneNetwork }) {
  const [seeds, setSeeds] = useState<number[]>([]);
  const [open, setOpen] = useState<Set<number>>(new Set());
  const [hover, setHover] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const svgRef = useRef<SVGSVGElement>(null);

  const index = useMemo(() => {
    const m = new Map<string, number>();
    g.nodes.forEach((n, i) => m.set(n, i));
    return m;
  }, [g]);

  const neighbours = useCallback(
    (i: number) => g.indices.slice(g.indptr[i], g.indptr[i + 1]),
    [g],
  );

  // Start on the first suggestion that exists, so the panel is never empty on arrival.
  useEffect(() => {
    if (seeds.length) return;
    const first = g.seedSuggestions.find((s) => index.has(s));
    if (first !== undefined) {
      const i = index.get(first) as number;
      setSeeds([i]);
      setOpen(new Set([i, ...neighbours(i).slice(0, 24)]));
    }
  }, [seeds.length, index, neighbours]);

  /** Random walk with restart over the OPEN subgraph. Recomputed whenever it grows. */
  const scores = useMemo(() => {
    const ids = [...open];
    const pos = new Map(ids.map((id, k) => [id, k]));
    const n = ids.length;
    if (!n) return new Map<number, number>();

    const restart = new Float64Array(n);
    const seedSet = seeds.filter((s) => pos.has(s));
    seedSet.forEach((s) => { restart[pos.get(s) as number] = 1 / seedSet.length; });
    if (!seedSet.length) restart.fill(1 / n);

    // Column-normalised adjacency restricted to the open set — the walker cannot leave the
    // subgraph the reader has actually opened, which is the honest thing for a partial view.
    const adj: number[][] = ids.map((id) =>
      [...neighbours(id)].filter((j) => pos.has(j)).map((j) => pos.get(j) as number));
    const deg = adj.map((a) => a.length || 1);

    let x = Float64Array.from(restart);
    for (let it = 0; it < ITERATIONS; it++) {
      const next = new Float64Array(n);
      for (let i = 0; i < n; i++) {
        const share = (ALPHA * x[i]) / deg[i];
        for (const j of adj[i]) next[j] += share;
      }
      for (let i = 0; i < n; i++) next[i] += (1 - ALPHA) * restart[i];
      x = next;
    }
    const max = Math.max(...x, 1e-12);
    return new Map(ids.map((id, k) => [id, x[k] / max]));
  }, [open, seeds, neighbours]);

  /** Radial by propagation score: the centre is where the walk concentrates. */
  const placed: Placed[] = useMemo(() => {
    const ids = [...open].sort((a, b) => (scores.get(b) ?? 0) - (scores.get(a) ?? 0));
    return ids.map((id, k) => {
      const s = scores.get(id) ?? 0;
      // A deterministic angle from the node id keeps a node in place as the graph grows.
      const angle = ((id * 2.399963) % (Math.PI * 2));
      const radius = k === 0 ? 0 : 60 + (1 - s) * 250 + (k % 7) * 6;
      return {
        id, score: s,
        x: 400 + Math.cos(angle) * radius,
        y: 300 + Math.sin(angle) * radius,
        r: 4 + Math.sqrt(g.degree[id]) * 1.1 + (seeds.includes(id) ? 4 : 0),
      };
    });
  }, [open, scores, seeds, g]);

  const placedById = useMemo(
    () => new Map(placed.map((p) => [p.id, p])), [placed]);

  const edges = useMemo(() => {
    const out: { a: Placed; b: Placed; w: number }[] = [];
    for (const p of placed) {
      const ns = neighbours(p.id);
      for (let k = 0; k < ns.length; k++) {
        const j = ns[k];
        if (j <= p.id) continue;
        const q = placedById.get(j);
        if (q) out.push({ a: p, b: q, w: g.weights[g.indptr[p.id] + k] });
      }
    }
    return out;
  }, [placed, placedById, neighbours, g]);

  const expand = (id: number) => {
    setOpen((prev) => {
      if (prev.size >= MAX_NODES) return prev;
      const next = new Set(prev);
      const ns = [...neighbours(id)]
        .sort((a, b) => g.degree[b] - g.degree[a])
        .slice(0, 18);
      for (const j of ns) {
        if (next.size >= MAX_NODES) break;
        next.add(j);
      }
      return next;
    });
  };

  const addSeed = (id: number) => {
    setSeeds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    setOpen((prev) => new Set([...prev, id, ...neighbours(id).slice(0, 12)]));
  };

  const reset = (name: string) => {
    const i = index.get(name);
    if (i === undefined) return;
    setSeeds([i]);
    setOpen(new Set([i, ...neighbours(i).slice(0, 24)]));
  };

  const matches = useMemo(() => {
    const q = query.trim().toUpperCase();
    if (q.length < 2) return [];
    return g.nodes.filter((n) => n.startsWith(q)).slice(0, 12);
  }, [query, g]);

  const frontier = useMemo(
    () => placed.filter((p) => {
      const ns = neighbours(p.id);
      return [...ns].some((j) => !open.has(j));
    }).length,
    [placed, open, neighbours]);

  const hoverNode = hover !== null ? hover : null;

  return (
    <div className={css.root}>
      <p className={css.premise}>{g.premise}</p>

      <div className={css.bar}>
        <div className={css.stats}>
          <Stat v={String(open.size)} l="open" />
          <Stat v={String(edges.length)} l="edges drawn" />
          <Stat v={String(frontier)} l="nodes with more to give" />
          <Stat v={`${g.stats.nodes.toLocaleString("en-US")}`} l="in the whole graph" dim />
        </div>

        <div className={css.search}>
          <input value={query} onChange={(e) => setQuery(e.target.value)}
                 placeholder="Start from a gene…" aria-label="Search for a gene to seed from" />
          {matches.length > 0 && (
            <div className={css.matches}>
              {matches.map((m) => (
                <button key={m} type="button" onClick={() => { reset(m); setQuery(""); }}>
                  {m}<span className={css.mDeg}>{g.degree[index.get(m) as number]}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className={css.suggest}>
        <span className={css.label}>Seed</span>
        {g.seedSuggestions.map((s) => (
          <button key={s} type="button" onClick={() => reset(s)}
                  className={seeds.includes(index.get(s) as number) ? css.sOn : css.s}>
            {s}
          </button>
        ))}
      </div>

      <div className={css.canvasWrap}>
        <svg ref={svgRef} viewBox="0 0 800 600" className={css.svg} role="img"
             aria-label="Gene network, expanded from the chosen seeds">
          {edges.map((e, i) => (
            <line key={i} x1={e.a.x} y1={e.a.y} x2={e.b.x} y2={e.b.y}
                  className={
                    hoverNode !== null && (e.a.id === hoverNode || e.b.id === hoverNode)
                      ? css.edgeHot : css.edge}
                  strokeWidth={Math.min(2.4, 0.4 + e.w * 0.3)} />
          ))}
          {placed.map((p) => (
            <g key={p.id}>
              <circle cx={p.x} cy={p.y} r={p.r}
                      className={seeds.includes(p.id) ? css.seed : css.node}
                      style={{ opacity: 0.35 + p.score * 0.65 }}
                      onClick={() => expand(p.id)}
                      onDoubleClick={() => addSeed(p.id)}
                      onMouseEnter={() => setHover(p.id)}
                      onMouseLeave={() => setHover(null)}>
                <title>
                  {g.nodes[p.id]} — degree {g.degree[p.id]}, named in{" "}
                  {g.diseaseCount[p.id]} diseases, propagation {p.score.toFixed(3)}
                  {"\n"}click to expand · double-click to add as a seed
                </title>
              </circle>
              {(p.score > 0.25 || seeds.includes(p.id)) && (
                <text x={p.x} y={p.y - p.r - 4} className={css.label2} textAnchor="middle">
                  {g.nodes[p.id]}
                </text>
              )}
            </g>
          ))}
        </svg>

        {hoverNode !== null && (
          <div className={css.tip}>
            <span className={css.tipName}>{g.nodes[hoverNode]}</span>
            <dl>
              <div><dt>degree</dt><dd>{g.degree[hoverNode]}</dd></div>
              <div><dt>diseases</dt><dd>{g.diseaseCount[hoverNode]}</dd></div>
              <div><dt>community</dt><dd>#{g.community[hoverNode]}</dd></div>
              <div>
                <dt>propagation</dt>
                <dd>{(scores.get(hoverNode) ?? 0).toFixed(3)}</dd>
              </div>
              <div>
                <dt>unopened neighbours</dt>
                <dd>{[...neighbours(hoverNode)].filter((j) => !open.has(j)).length}</dd>
              </div>
            </dl>
          </div>
        )}
      </div>

      <p className={css.how}>
        <strong>Click a node to expand it.</strong> Double-click to make it a seed — the walk
        restarts from every seed at once, so two seeds ask which genes sit between them.
        Distance from the centre is the propagation score, not a layout artefact: the centre is
        where a random walk that keeps returning to the seeds spends its time. The walk runs
        over the OPEN subgraph only, so the numbers change as you open more — which is the
        honest behaviour for a partial view of a graph with{" "}
        {g.stats.nodes.toLocaleString("en-US")} nodes and{" "}
        {g.stats.edges.toLocaleString("en-US")} edges.
      </p>

      <p className={css.provenance}>
        Built from the HPO gene-to-disease file: two genes are adjacent when they are named in
        a common disease, and the edge weight is how many. {g.communities.toLocaleString("en-US")}{" "}
        communities at modularity {g.modularity}. The same graph is the one measured on the
        sparse-structure tab — this is the object, that is its geometry.
      </p>
    </div>
  );
}

function Stat({ v, l, dim }: { v: string; l: string; dim?: boolean }) {
  return (
    <div className={dim ? css.statDim : css.stat}>
      <span className={css.statV}>{v}</span>
      <span className={css.statL}>{l}</span>
    </div>
  );
}
