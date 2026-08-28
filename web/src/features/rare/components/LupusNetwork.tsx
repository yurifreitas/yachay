/** Lupus as a network, and the question a network answers that a table cannot.
 *
 *  THE QUESTION. "Given this gene, is there anything that reaches it?" That is a **path**
 *  query — a composition of edges — and a table has no composition. It can tell you which
 *  cell a gene acts in, and separately which cell a therapy targets, and leave the reader
 *  to trace the join by eye across two lists.
 *
 *  So the reachability is computed in `tools/lupus_graph.py` and the result is the
 *  headline of this view rather than a rendering detail:
 *
 *    · one gene has no path to any therapy at all;
 *    · seven of eleven cell types have nothing pointed at them;
 *    · four of eight mechanisms have nothing pointed at them — including **complement**
 *      and **clearance**, the two with the strongest monogenic evidence in the disease.
 *
 *  FORM. A force-directed graph with four node categories. Force layout is the right form
 *  when the structure is unknown and the question is connectivity; it is the wrong form
 *  for reading exact values, which is why every number on this page is in the panel beside
 *  it rather than encoded in the picture. Node size is degree, so a hub looks like a hub.
 *
 *  READ ALOUD: circles are genes, squares are mechanisms, diamonds are cell types,
 *  triangles are therapies. A line means "acts in", "plays out in", or "targets". Click a
 *  node to isolate it and its neighbours, and to see the shortest path from it to a
 *  therapy — or that there is none.
 */
import { useMemo, useState } from "react";
import { EChart } from "../../../components/organisms/EChart";
import { categorical, chartInk, type Mode } from "../../../lib/palette";
import { lupusGraph } from "../data/lupusGraph";
import { Chip } from "../../../components/atoms/Chip";
import { StatusDot } from "../../../components/atoms/StatusDot";
import css from "./LupusNetwork.module.css";

type Kind = "gene" | "mechanism" | "cell" | "therapy";

const KINDS: { id: Kind; label: string; symbol: string }[] = [
  { id: "gene", label: "Gene", symbol: "circle" },
  { id: "mechanism", label: "Mechanism", symbol: "rect" },
  { id: "cell", label: "Cell type", symbol: "diamond" },
  { id: "therapy", label: "Therapy", symbol: "triangle" },
];

const EVIDENCE_TONE: Record<string, "known" | "partial" | "unknown"> = {
  monogenic: "known",
  both: "known",
  gwas: "partial",
  candidate: "unknown",
};

export function LupusNetwork() {
  const [focus, setFocus] = useState<string | null>(null);
  const [hidden, setHidden] = useState<Set<Kind>>(new Set());
  const [onlyUnreached, setOnlyUnreached] = useState(false);

  const g = lupusGraph;
  const all = useMemo(
    () => [...g.nodes.genes, ...g.nodes.mechanisms, ...g.nodes.cells, ...g.nodes.therapies],
    [g]
  );
  const byId = useMemo(() => new Map(all.map((n) => [n.id, n])), [all]);
  const degree = useMemo(() => {
    const d = new Map<string, number>();
    g.edges.forEach((e) => {
      d.set(e.source, (d.get(e.source) ?? 0) + 1);
      d.set(e.target, (d.get(e.target) ?? 0) + 1);
    });
    return d;
  }, [g]);

  const selected = focus ? byId.get(focus) : null;

  const build = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const [cGene, cMech, cCell, , cUnreached, cTher] = categorical(mode);
      const colour: Record<Kind, string> = {
        gene: cGene, mechanism: cMech, cell: cCell, therapy: cTher,
      };

      const visible = all.filter((n) => {
        if (hidden.has(n.kind as Kind)) return false;
        if (onlyUnreached && n.kind === "gene" && (n as { reachable?: boolean }).reachable) return false;
        return true;
      });
      const visibleIds = new Set(visible.map((n) => n.id));

      return {
        animation: true,
        animationDuration: 300,
        tooltip: {
          formatter: (o: { dataType: string; data: Record<string, unknown> }) => {
            if (o.dataType === "edge") return String(o.data.kind ?? "").replace(/_/g, " ");
            const n = byId.get(String(o.data.id));
            if (!n) return "";
            const bits = [`<strong>${n.name}</strong> · ${n.kind}`];
            if ("note" in n && n.note) bits.push(`<span style="opacity:.75">${n.note}</span>`);
            if ("role" in n && n.role) bits.push(`<span style="opacity:.75">${n.role}</span>`);
            bits.push(`<span style="opacity:.6">${degree.get(n.id) ?? 0} connections</span>`);
            return bits.join("<br/>");
          },
          extraCssText: "max-width:330px;white-space:normal;line-height:1.55",
        },
        legend: { show: false },
        series: [
          {
            type: "graph",
            layout: "force",
            roam: true,
            draggable: true,
            force: { repulsion: 210, edgeLength: [50, 130], gravity: 0.09, friction: 0.22 },
            // Focus on hover dims everything not adjacent — the cheapest way to read a
            // neighbourhood out of a hairball.
            emphasis: { focus: "adjacency", scale: 1.1, lineStyle: { width: 3 } },
            selectedMode: "single",
            select: { itemStyle: { borderColor: ink.text, borderWidth: 3 } },
            label: {
              show: true, position: "right", fontSize: 11, color: ink.muted,
              formatter: (o: { data: { name: string; kind: string } }) =>
                o.data.kind === "gene" || o.data.kind === "therapy" ? o.data.name : "",
            },
            categories: KINDS.map((k) => ({ name: k.label })),
            data: visible.map((n) => {
              const unreached =
                n.kind === "gene" && !(n as { reachable?: boolean }).reachable;
              const deg = degree.get(n.id) ?? 1;
              return {
                id: n.id,
                name: n.name,
                kind: n.kind,
                category: KINDS.findIndex((k) => k.id === n.kind),
                symbol: KINDS.find((k) => k.id === n.kind)!.symbol,
                symbolSize: Math.min(46, 11 + Math.sqrt(deg) * 5),
                itemStyle: {
                  color: unreached ? cUnreached : colour[n.kind as Kind],
                  borderColor: unreached ? cUnreached : "transparent",
                  borderWidth: unreached ? 3 : 0,
                  opacity: 0.95,
                },
              };
            }),
            links: g.edges
              .filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target))
              .map((e) => ({
                source: e.source,
                target: e.target,
                kind: e.kind,
                lineStyle: {
                  color: ink.muted,
                  opacity: e.kind === "plays_in" ? 0.16 : 0.34,
                  width: e.kind === "targets" || e.kind === "modulates" ? 1.6 : 1,
                  curveness: 0.06,
                },
              })),
          },
        ],
      };
    },
    [all, byId, degree, g.edges, hidden, onlyUnreached]
  );

  const toggleKind = (k: Kind) =>
    setHidden((s) => {
      const next = new Set(s);
      next.has(k) ? next.delete(k) : next.add(k);
      return next;
    });

  const a = g.analysis;

  return (
    <div className={css.root}>
      {/* ---- the analytical result, before the picture ------------------------- */}
      <div className={css.findings}>
        <Finding
          n={a.unreachableGenes.length}
          label="gene with no path to any therapy"
          detail={a.unreachableGenes.join(", ") || "none"}
          tone="unknown"
        />
        <Finding
          n={a.cellsWithNoTherapy.length}
          of={g.summary.cells}
          label="cell types nothing targets"
          detail={a.cellsWithNoTherapy
            .map((id) => byId.get(id)?.name ?? id)
            .join(" · ")}
          tone="unknown"
        />
        <Finding
          n={a.mechanismsWithNoTherapy.length}
          of={g.summary.mechanisms}
          label="mechanisms nothing targets"
          detail={a.mechanismsWithNoTherapy
            .map((id) => byId.get(id)?.name ?? id)
            .join(" · ")}
          tone="unknown"
        />
        <Finding
          n={g.summary.edges}
          label="edges over 4 node kinds"
          detail={`${g.summary.genes} genes · ${g.summary.mechanisms} mechanisms · ${g.summary.cells} cells · ${g.summary.therapies} therapies`}
          tone="neutral"
        />
      </div>

      <p className={css.headline}>
        <strong>Complement and clearance have nothing pointed at them</strong> — the two
        mechanisms with the strongest monogenic evidence in the disease. C1q deficiency is
        the strongest single-gene risk for lupus known, and failed clearance of dying cells
        is where the antigen comes from. The field treats the <em>amplifier</em>
        {" "}(interferon) and the <em>effector</em> (the B cell), not the initiating defect.
      </p>

      <div className={css.body}>
        {/* ---- the graph ------------------------------------------------------- */}
        <div className={css.graph}>
          <div className={css.controls}>
            {KINDS.map((k) => (
              <button
                key={k.id}
                type="button"
                className={hidden.has(k.id) ? css.chipOff : css.chip}
                aria-pressed={!hidden.has(k.id)}
                onClick={() => toggleKind(k.id)}
              >
                <span className={`${css.swatch} ${css[k.id]}`} aria-hidden="true" />
                {k.label}
              </button>
            ))}
            <label className={css.check}>
              <input
                type="checkbox"
                checked={onlyUnreached}
                onChange={(e) => setOnlyUnreached(e.target.checked)}
              />
              Only genes nothing reaches
            </label>
          </div>
          <EChart
            build={build}
            height={620}
            deps={[hidden, onlyUnreached]}
            ariaLabel={`Force-directed network of ${g.summary.genes} lupus genes, ${g.summary.mechanisms} mechanisms, ${g.summary.cells} cell types and ${g.summary.therapies} therapies, with ${g.summary.edges} edges. ${a.unreachableGenes.length} gene has no path to a therapy.`}
          />
          <p className={css.readAloud}>
            Circles are genes, squares mechanisms, diamonds cell types, triangles therapies.
            Node size is the number of connections. Hover to isolate a neighbourhood; drag to
            pull a node out of the tangle; scroll to zoom.
          </p>
        </div>

        {/* ---- the inspector --------------------------------------------------- */}
        <aside className={css.panel}>
          <h4 className={css.panelTitle}>Trace a gene to a therapy</h4>
          <p className={css.panelNote}>
            The shortest path from a gene to something that acts on it — or the statement
            that there is none.
          </p>
          <div className={css.geneList}>
            {g.nodes.genes.map((gene) => (
              <button
                key={gene.id}
                type="button"
                className={focus === gene.id ? css.geneOn : css.gene}
                onClick={() => setFocus(focus === gene.id ? null : gene.id)}
              >
                <span className={css.geneName}>{gene.name}</span>
                <span className={css.geneHops}>
                  {gene.reachable ? `${gene.hops} hops` : "no path"}
                </span>
              </button>
            ))}
          </div>

          {selected && "path" in selected && (
            <div className={css.detail}>
              <div className={css.detailHead}>
                <span className={css.detailName}>{selected.name}</span>
                <Chip tone={EVIDENCE_TONE[(selected as { evidence: string }).evidence]}>
                  {(selected as { evidence: string }).evidence}
                </Chip>
                <Chip tone={(selected as { effect: string }).effect === "gain" ? "unknown" : undefined}>
                  {(selected as { effect: string }).effect} of function
                </Chip>
              </div>
              <p className={css.detailNote}>{(selected as { note: string }).note}</p>
              {(selected as { path: string[] }).path.length ? (
                <ol className={css.path}>
                  {(selected as { path: string[] }).path.map((id, i) => {
                    const n = byId.get(id);
                    return (
                      <li key={id} className={css.pathStep}>
                        <span className={`${css.swatch} ${css[(n?.kind ?? "gene") as Kind]}`} />
                        <span className={css.pathName}>{n?.name ?? id}</span>
                        <span className={css.pathKind}>{n?.kind}</span>
                        {i < (selected as { path: string[] }).path.length - 1 && (
                          <span className={css.arrow} aria-hidden="true">↓</span>
                        )}
                      </li>
                    );
                  })}
                </ol>
              ) : (
                <p className={css.noPath}>
                  <StatusDot state="unknown" label="no path" size="sm" /> Nothing in this
                  graph reaches {selected.name}: neither its mechanism nor its cell type has
                  a therapy pointed at it.
                </p>
              )}
            </div>
          )}
        </aside>
      </div>

      <p className={css.provenance}>
        <strong>What &ldquo;reaches&rdquo; means here.</strong> A gene reaches a therapy when
        a path exists through a shared cell type or mechanism. That is a screening question,
        not a claim of druggability — sharing a cell type with an approved antibody does not
        make a gene a target. It produces a shortlist of gaps, which is what this repository
        is for. {g.provenance}
      </p>
    </div>
  );
}

function Finding({
  n, of, label, detail, tone,
}: { n: number; of?: number; label: string; detail: string; tone: "unknown" | "neutral" }) {
  return (
    <article className={`${css.finding} ${tone === "unknown" ? css.findingWarn : ""}`}>
      <span className={css.findingN}>
        {n}
        {of !== undefined && <span className={css.findingOf}> / {of}</span>}
      </span>
      <span className={css.findingLabel}>{label}</span>
      <span className={css.findingDetail}>{detail}</span>
    </article>
  );
}
