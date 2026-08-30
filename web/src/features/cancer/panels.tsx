import { useMemo } from "react";
import { identityScale } from "../../lib/palette";
import {
  DEFAULT_REGISTERED, LEVEL_LABEL, cancellation, controls, footprints, gateInputs, privateCount, regate,
  type CancerLevel, type Gates, type Subgroup,
} from "../../lib/cancerModel";
import GateControls, { useGates } from "./GateControls";
import s from "./CancerPage.module.css";

/** The cancer page's panels, lifted out of the page.
 *
 *  A registry that feeds a page cannot import from that page — that is a cycle, and it is
 *  the same wall the gene page hit when it was migrated. Its panels moved to genePanels.tsx
 *  for the same reason; these move here.
 *
 *  Nothing else changed. The point of a migration is a move, not a rewrite: every panel
 *  keeps its markup, its comments and its behaviour, so a diff on this file is a diff about
 *  where the code lives rather than about what it draws.
 */

/** Grouped thousands, pinned to the page's own language rather than the reader's browser.
 *  `toLocaleString()` with no argument rendered 1242 as "1.242" under a pt-BR browser, which
 *  inside an English sentence reads as a decimal. The prose here is English; so is its
 *  number formatting. */
const fmt = (n: number) => n.toLocaleString("en-US");

export type Split = NonNullable<ReturnType<typeof cancellation>>;

/* ------------------------------------------------------------------ KPI row */

export function Kpis({ data }: { data: CancerLevel }) {
  const c = controls(data);
  const back = c.filter((x) => x.rank !== null).length;
  const tiles = [
    { n: data.scale.subgroups, label: "subgroups", note: `at least 8 screened lines` },
    {
      n: data.scale.powered, label: "can detect 0.8 SD",
      note: `${data.scale.underpowered} cannot, and are marked rather than dropped`,
      tone: "good" as const,
    },
    {
      n: data.scale.panEssentialDropped, label: "pan-essentials removed",
      note: "Stage 3, before ranking rather than after", tone: "warn" as const,
    },
    {
      n: c.length ? `${back}/${c.length}` : "—", label: "positive controls back",
      note: "textbook lineage dependencies, recovered blind",
    },
  ];
  return (
    <div className={s.kpis}>
      {tiles.map((t) => (
        <div key={t.label} className={s.kpi} data-tone={t.tone}>
          <span className={s.kpiN}>{typeof t.n === "number" ? fmt(t.n) : t.n}</span>
          <span className={s.kpiL}>{t.label}</span>
          <span className={s.kpiNote}>{t.note}</span>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------ the finding that justifies the level switch */

export function Cancellation({ split }: { split: Split }) {
  return (
    <div className={s.finding}>
      <p className={s.findingTag}>Why the grouping is the analysis</p>
      <h3>
        Pooled <strong>Lung</strong> has {split.pooled.lines} screened lines — the best-powered
        subgroup here — and returns <strong>nothing</strong>.
      </h3>
      <p>
        Split at the subtype level, both halves light up, each with the genes its biology
        predicts. They were cancelling: a dependency present in one half and absent in the
        other averages to no difference from everything else. A null result at the coarse
        level is not evidence of no dependency; it can be evidence of the wrong grouping.
      </p>
      <div className={s.splitRow}>
        {split.parts.map((p) => (
          <div key={p.subgroup} className={s.splitCard}>
            <span className={s.splitName}>{p.subgroup}</span>
            <span className={s.splitMeta}>{p.lines} lines · {p.hitCount} hits</span>
            <span className={s.splitGenes}>
              {p.hits.slice(0, 5).map((h) => h.gene).join(" · ")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
export function SubgroupPicker(
  { groups, chosen, onPick }:
  { groups: Subgroup[]; chosen: Subgroup; onPick: (v: string) => void },
) {
  return (
    <div className={s.levels}>
      <label className={s.pickerLabel}>
        Subgroup{" "}
        <select value={chosen.subgroup} onChange={(e) => onPick(e.target.value)}>
          {groups.map((g) => (
            <option key={g.subgroup} value={g.subgroup}>
              {g.subgroup} ({fmt(g.lines)} lines)
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

/* --------------------------------------------------- panel 1: what could be seen at all */

export function Power(
  { groups, chosen, onPick }:
  { groups: Subgroup[]; chosen: Subgroup; onPick: (v: string) => void },
) {
  const colours = useMemo(
    () => identityScale(groups.map((g) => g.subgroup)), [groups]);
  const maxLines = Math.max(...groups.map((g) => g.lines));

  return (
    <section className={s.panel}>
      <h3>Which subgroups could detect anything, and which only look empty</h3>
      <p className={s.sub}>
        Bar length is the smallest effect the subgroup&rsquo;s size can detect, from{" "}
        <code>sieve.stages.power</code>. Below the marked line a subgroup can see a large
        effect; above it, an empty result means the screen could not resolve one — not that
        none exists. Click to inspect.
      </p>
      <ul className={s.powerList}>
        {groups.map((g) => (
          <li key={g.subgroup}>
            <button
              className={g.subgroup === chosen.subgroup ? s.rowOn : s.row}
              onClick={() => onPick(g.subgroup)}
              aria-pressed={g.subgroup === chosen.subgroup}
            >
              <span className={s.swatch} style={{ background: colours[g.subgroup] }} />
              <span className={s.rowName}>{g.subgroup}</span>
              <span className={s.rowBarWrap}>
                <span
                  className={s.rowBar}
                  style={{ width: `${(g.lines / maxLines) * 100}%`,
                           background: colours[g.subgroup] }}
                />
              </span>
              <span className={s.rowNum}>{g.lines}</span>
              <span className={g.powered ? s.floorOk : s.floorBad}>
                {g.detectableFloor?.toFixed(2) ?? "—"}
              </span>
              <span className={g.hitCount ? s.hits : s.hitsNone}>
                {g.powered
                  ? `${g.hitCount} hit${g.hitCount === 1 ? "" : "s"}`
                  : "underpowered"}
              </span>
            </button>
          </li>
        ))}
      </ul>
      <p className={s.axisNote}>
        columns: screened lines · smallest detectable effect (SD) · result
      </p>
    </section>
  );
}

/** The gates and the panel they govern, kept adjacent: a control whose effect is off-screen
 *  is a control nobody trusts. */
export function Gated(
  { group, level, registered }:
  { group: Subgroup; level: string; registered: typeof DEFAULT_REGISTERED },
) {
  const [gates, set, dirty, reset] = useGates(registered);
  const { rows, total } = regate(group, gates);
  return (
    <>
      <GateControls gates={gates} set={set} dirty={dirty} reset={reset} reg={registered}
                    kept={rows.length} total={total} rows={gateInputs(group)} />
      <Detail group={group} level={level} rows={rows} gates={gates} dirty={dirty} />
    </>
  );
}

/* ------------------------------------------- panel 2: the chosen subgroup, both ends shown */

export function Detail(
  { group, level, rows, gates, dirty }:
  { group: Subgroup; level: string; rows: Subgroup["hits"]; gates: Gates; dirty: boolean },
) {
  const span = useMemo(() => {
    const all = rows.flatMap((h) => [h.meanInGroup, h.meanElsewhere]);
    // Padded by 4 % at each end: without it the gene at the maximum lands at left:100% and
    // is drawn half outside the track.
    const lo = Math.min(0, ...all), hi = Math.max(1, ...all), pad = (hi - lo) * 0.04;
    return { lo: lo - pad, hi: hi + pad };
  }, [rows]);
  const x = (v: number) => ((v - span.lo) / (span.hi - span.lo)) * 100;

  return (
    <section className={s.panel}>
      <h3>
        {group.subgroup}
        <span className={s.badge}>{LEVEL_LABEL[level]}</span>
        {dirty && <span className={s.badgeMoved}>re-gated</span>}
      </h3>
      <p className={s.sub}>{group.says}</p>

      {rows.length === 0 ? (
        <p className={s.empty}>
          {dirty
            ? "Nothing clears the gates as you have set them. Widen a threshold, or restore "
              + "the registered values above \u2014 an empty list at settings chosen after "
              + "seeing the data says something about the settings, not about this subgroup."
            : group.powered
            ? "No gene cleared the gates here. With this many lines the screen could have "
              + "resolved a large effect, so this is a measured absence rather than a blind spot."
            : "Nothing to draw, and nothing to conclude: this subgroup is too small to have "
              + "detected a large effect had one been present."}
        </p>
      ) : (
        <>
          <p className={s.sub}>
            Each row is a dumbbell: the hollow end is the gene&rsquo;s mean dependency{" "}
            <em>everywhere else</em>, the filled end is its mean <em>inside this subgroup</em>.
            Both ends are drawn because the gap alone does not make a target — the filled end
            must also be a real dependency. That is the Stage 0 gate, and it is here because
            an earlier version of this analysis lacked it and ranked genes the rest of the
            panel depended on more.
          </p>
          <ul className={s.dumbbells}>
            {rows.map((h) => (
              <li key={h.gene}>
                <span className={s.gene}>{h.gene}</span>
                <span className={s.track}>
                  <span className={s.zero} style={{ left: `${x(gates.floor)}%` }} />
                  <span
                    className={s.link}
                    style={{
                      left: `${Math.min(x(h.meanElsewhere), x(h.meanInGroup))}%`,
                      width: `${Math.abs(x(h.meanInGroup) - x(h.meanElsewhere))}%`,
                    }}
                  />
                  <span className={s.dotOpen} style={{ left: `${x(h.meanElsewhere)}%` }}
                        title={`elsewhere ${h.meanElsewhere.toFixed(3)}`} />
                  <span className={s.dotFull} style={{ left: `${x(h.meanInGroup)}%` }}
                        title={`in group ${h.meanInGroup.toFixed(3)}`} />
                </span>
                <span className={s.d}>{h.d.toFixed(2)}</span>
                <span className={s.q}>
                  q&nbsp;{h.q < 1e-4 ? h.q.toExponential(0) : h.q.toFixed(4)}
                </span>
              </li>
            ))}
          </ul>
          <p className={s.axisNote}>
            dashed line: the {gates.floor.toFixed(2)} dependency floor a filled end must clear · columns: Cohen&rsquo;s
            d, then the Benjamini&ndash;Hochberg q within this subgroup
          </p>
        </>
      )}
    </section>
  );
}

/* ---------------------------------------- panel 3: private to a cancer, or shared across */

export function Shared({ data }: { data: CancerLevel }) {
  const shared = useMemo(() => footprints(data).slice(0, 14), [data]);
  const priv = useMemo(() => privateCount(data), [data]);
  const colours = useMemo(
    () => identityScale(data.results.map((r) => r.subgroup)), [data]);

  if (!shared.length) {
    return (
      <section className={s.panel}>
        <h3>Private or shared</h3>
        <p className={s.empty}>
          Every hit at this level appears in exactly one subgroup, so there is no shared
          structure to draw.
        </p>
      </section>
    );
  }

  return (
    <section className={s.panel}>
      <h3>Private to one cancer, or shared across several</h3>
      <p className={s.sub}>
        A target list cannot answer this on its own, and the difference decides what a therapy
        would have to be selective against. <strong>{priv}</strong> genes are private to a
        single subgroup; these {shared.length} recur, which puts them closer to a pathway than
        to a lineage vulnerability.
      </p>
      <ul className={s.shared}>
        {shared.map((f) => (
          <li key={f.gene}>
            <span className={s.gene}>{f.gene}</span>
            <span className={s.chips}>
              {f.groups.map((g) => (
                <span
                  key={g.subgroup} className={s.chip}
                  style={{ borderColor: colours[g.subgroup] }}
                >
                  <span className={s.chipDot} aria-hidden="true"
                        style={{ background: colours[g.subgroup] }} />
                  {g.subgroup} <b>{g.d.toFixed(1)}</b>
                </span>
              ))}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/* --------------------------------------------------------------- panel 4: the controls */

export function Controls({ data }: { data: CancerLevel }) {
  const rows = controls(data);
  if (!rows.length) return null;
  const back = rows.filter((r) => r.rank !== null).length;
  return (
    <section className={s.panel}>
      <h3>Positive controls, reported whole</h3>
      <p className={s.sub}>
        Textbook lineage dependencies named in the analysis before it ran, checked on every
        run. <strong>{back} of {rows.length}</strong> came back. The {rows.length - back} that
        did not are listed with their result rather than folded into a pass rate, because a
        single percentage would let a specific failure read as noise.
      </p>
      <table className={s.table}>
        <thead>
          <tr><th>Subgroup</th><th>Control</th><th>Rank in the shortlist</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.subgroup}-${r.gene}`}>
              <td>{r.subgroup}</td>
              <td><code>{r.gene}</code></td>
              <td className={r.rank === null ? s.miss : s.got}>
                {r.rank === null ? "not recovered" : `#${r.rank + 1}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
