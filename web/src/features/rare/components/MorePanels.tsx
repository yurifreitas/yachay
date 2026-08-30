import gapsRaw from "../../../data/generated/gap_taxonomy.json";
import attentionRaw from "../../../data/generated/attention_burden.json";
import autismRaw from "../../../data/generated/autism_convergence.json";
import voidRaw from "../../../data/generated/knowledge_void.json";
import { useT } from "../../../i18n";
import { MORE } from "../../../i18n/more";
import { fmtInt } from "../../../lib/scale";
import { Provenance } from "./Provenance";
import css from "./MeasuredPanels.module.css";

/** FOUR MEASUREMENTS THAT WERE RENDERED NOWHERE.
 *
 *  gap_taxonomy, attention_burden, autism_convergence and knowledge_void were all computed,
 *  verified, and drawn in no interface — the failure `web/scripts/build-data.mjs` names in
 *  its own comment and audit A29 names in prose: *a dashboard that publishes twenty
 *  aggregate layers while its strongest result sits in a JSON file is publishing that result
 *  nowhere.*
 *
 *  They are here now because ADR 0009 made adding a section one entry instead of an edit in
 *  four places. That is the return on the refactor, and the reason it was worth the churn.
 *
 *  EVERY PANEL LEADS WITH WHAT ITS MEASUREMENT REFUSES TO SAY. The gap taxonomy cannot tell
 *  "nobody looked" from "the biology forbids it". The attention panel reports no severity
 *  coefficient because the column is degenerate. The autism panel carries no z on any gene
 *  because the domain failed the adapter gate. Each of those is in the panel, not a footnote.
 */

const pct = (v: number, d = 1) => `${(100 * v).toFixed(d)} %`;

/** A signed statistic on a zero-centred track, so a negative reads as a DIRECTION and not as
 *  a smaller positive one. Both new panels need it and both would otherwise invent it. */
function SignedRow(
  { label, value, cap, fmt, flag }:
  { label: string; value: number; cap: number; fmt: string; flag?: string },
) {
  const w = Math.min(50, (50 * Math.abs(value)) / cap);
  return (
    <div className={css.corrRow}>
      <span className={css.corrLabel}>
        {label}
        {flag ? <><br /><span className={css.corrFlag}>{flag}</span></> : null}
      </span>
      <span className={css.corrTrack}>
        <span className={css.corrZero} />
        <span className={value < 0 ? `${css.corrBar} ${css.corrBarNeg}` : css.corrBar}
              style={{ left: value < 0 ? `${50 - w}%` : "50%", width: `${w}%` }} />
      </span>
      <span className={css.corrVal}>{fmt}</span>
    </div>
  );
}

/* ================================================================== the typed gap */

export function GapTaxonomy() {
  const tt = useT();
  const d = gapsRaw as any;
  const totals: Record<string, number> = d.totals ?? {};
  const shares: Record<string, number> = d.shares ?? {};
  const byField: Record<string, Record<string, number>> = d.by_field ?? {};
  const kinds = ["accessibility", "epistemic", "interoperability", "population"];

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{fmtInt(totals.interoperability ?? 0)}</span>
        <p><strong>{tt(MORE.gapHeading)}</strong> {tt(MORE.gapSub)}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>
          {fmtInt(d.scale?.field_gaps ?? 0)} field gaps over {fmtInt(d.scale?.diseases ?? 0)} diseases
        </span>
        <div className={css.split} role="img" aria-label="the four kinds of gap, by share">
          {kinds.map((k) => (
            <span key={k} className={k === "interoperability" ? css.splitA : css.splitB}
                  style={{ width: `${100 * (shares[k] ?? 0)}%` }} />
          ))}
        </div>
        <div className={css.splitLegend}>
          {kinds.map((k) => (
            <span key={k} className={css.legendItem}>
              <span className={`${css.swatch} ${k === "interoperability" ? css.swatchA : css.swatchB}`} />
              <span className={css.legendVal}>{pct(shares[k] ?? 0)}</span>
              <span className={css.legendText}>{k}</span>
            </span>
          ))}
        </div>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>kind</th><th>gaps</th><th>what would close it</th></tr>
            </thead>
            <tbody>
              {kinds.map((k) => (
                <tr key={k}>
                  <td className={css.tdName}>{k}</td>
                  <td>{fmtInt(totals[k] ?? 0)}</td>
                  <td className={css.tdMuted}>{(d.kinds ?? {})[k]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.caveat}>{(d.kinds ?? {}).model}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>by field — where each kind of hole actually sits</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>field</th>{kinds.map((k) => <th key={k}>{k.slice(0, 9)}</th>)}</tr>
            </thead>
            <tbody>
              {Object.entries(byField).map(([field, row]) => (
                <tr key={field}>
                  <td className={css.tdName}>{field.replace(/_/g, " ")}</td>
                  {kinds.map((k) => (
                    <td key={k} className={k === "interoperability" ? undefined : css.tdMuted}>
                      {row[k] ? fmtInt(row[k]) : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>{tt(MORE.gapFields)}</p>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.instrument}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ================================================================== attention vs burden */

export function AttentionBurden() {
  const tt = useT();
  const d = attentionRaw as any;
  const arms: any[] = d.arms ?? [];
  const neglected: any[] = d.most_neglected ?? [];
  const attended: any[] = d.most_attended ?? [];

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>+{(arms[0]?.attention_vs_prevalence ?? 0).toFixed(3)}</span>
        <p><strong>{tt(MORE.attHeading)}</strong> {tt(MORE.attSub)}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>the confound measured, not disclaimed</span>
        <p className={css.blockSub}>{d.method?.confound}</p>
        <div className={css.corr}>
          {arms.map((a) => (
            <SignedRow key={a.label} label={a.label} value={a.attention_vs_prevalence}
                       cap={0.5} fmt={`+${a.attention_vs_prevalence.toFixed(3)}`}
                       flag={`${fmtInt(a.diseases)} diseases · [${a.attention_vs_prevalence_ci95.join(", ")}]`} />
          ))}
        </div>
        <p className={css.note}>{d.method?.statistic}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>the arm this instrument cannot report</span>
        <p className={css.caveat}>{arms[0]?.severity_unavailable}</p>
        <p className={css.note}>{d.the_third_sighting}</p>
      </div>

      <div className={css.pair}>
        {([[tt(MORE.attNeglected), neglected], ["and the most attended", attended]] as const).map(
          ([title, rows]) => (
            <div key={title} className={css.block}>
              <span className={css.blockK}>{title}</span>
              <div className={css.tableWrap}>
                <table className={css.table}>
                  <thead>
                    <tr><th>disorder</th><th>citations</th><th>top gene</th><th>index</th></tr>
                  </thead>
                  <tbody>
                    {rows.slice(0, 10).map((r: any) => (
                      <tr key={r.disease}>
                        <td className={css.tdName}>{r.disease}</td>
                        <td>{fmtInt(r.citations)}</td>
                        <td className={css.tdMuted}>{r.top_gene}</td>
                        <td className={css.tdMuted}>{r.attention_index}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ),
        )}
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.method}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ================================================================== autism convergence */

export function AutismConvergence() {
  const tt = useT();
  const d = autismRaw as any;
  const arms = Object.entries(d.convergence ?? {}) as [string, any][];
  const cap = Math.max(5, ...arms.map(([, a]) => Math.abs(a.z)));

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{fmtInt(d.scale?.genes ?? 0)}</span>
        <p><strong>{tt(MORE.autHeading)}</strong> {tt(MORE.autSub)}</p>
      </div>

      <p className={css.caveat}>{d.not_an_adapter?.consequence}</p>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MORE.autPrior)}</span>
        <p className={css.blockSub}>{d.prior_stated_before_the_measurement}</p>
        <div className={css.corr}>
          {arms.map(([label, a]) => (
            <SignedRow key={label} label={label.replace(/_/g, " ")} value={a.z} cap={cap}
                       fmt={`${a.z > 0 ? "+" : ""}${a.z} z`}
                       flag={`${a.observed} observed · ${a.null_mean} under ${a.draws} permutations`} />
          ))}
        </div>
        <p className={css.note}>{d.verdict}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MORE.autCommonest)}</span>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statK}>cell types</span>
            {(d.commonest?.cell_types ?? []).slice(0, 6).map((c: any) => (
              <span key={c.name} className={css.statNote}>{c.genes} · {c.name}</span>
            ))}
          </div>
          <div className={css.stat}>
            <span className={css.statK}>pathways</span>
            {(d.commonest?.pathways ?? []).slice(0, 6).map((p: any) => (
              <span key={p.id} className={css.statNote}>{p.genes} · {p.id}</span>
            ))}
          </div>
        </div>
        <p className={css.caveat}>{d.caveat_on_the_top_cell_type}</p>
      </div>

      <p className={css.note}>{d.chain}</p>

      <Provenance generated={d.generated} provenance={d.provenance}
                  method={d.not_an_adapter} says={d.says} limits={d.limits} />
    </div>
  );
}

/* ================================================================== the absent combinations */

/** The lattice picture already ships inside the shape section. This is the part that picture
 *  cannot carry: WHICH combinations are absent, said in words. A cell is five band names, and
 *  five band names is a sentence a clinician can disagree with — a heat cell is not. */
export function VoidCells() {
  const tt = useT();
  const d = voidRaw as any;
  const axes: string[] = d.lattice?.axes ?? [];
  const anti: any[] = d.antiforms?.cells ?? [];
  const densest: any[] = d.densest ?? [];

  const reads = (r: Record<string, string>) => axes.map((a) => r?.[a] ?? "—");

  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{fmtInt(d.antiforms?.count ?? 0)}</span>
        <p><strong>{tt(MORE.voidHeading)}</strong> {tt(MORE.voidSub)}</p>
      </div>

      <div className={css.pair}>
        <div className={css.stat}>
          <span className={css.statVal}>{fmtInt(d.occupied?.cells ?? 0)}</span>
          <span className={css.statK}>of {fmtInt(d.lattice?.cells ?? 0)} cells occupied</span>
          <span className={css.statNote}>
            [{(d.occupied?.ci95 ?? []).join(", ")}] · {d.occupied?.z_vs_null} z against a null
            that shuffles each axis independently
          </span>
        </div>
        <div className={css.stat}>
          <span className={css.statVal}>{pct(d.shape?.frontier_share ?? 0)}</span>
          <span className={css.statK}>of occupied cells are on the frontier</span>
          <span className={css.statNote}>
            {fmtInt(d.shape?.interior_cells ?? 0)} interior cells only — what is known is a
            filament, not a solid
          </span>
        </div>
        <div className={css.stat}>
          <span className={css.statVal}>
            {fmtInt(Math.round(d.antiforms?.diseases_expected_in_them ?? 0))}
          </span>
          <span className={css.statK}>diseases the marginals put in empty cells</span>
          <span className={css.statNote}>{d.antiforms?.reading}</span>
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MORE.voidAntiTable)}</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>expected</th>{axes.map((a) => <th key={a}>{a.replace(/_/g, " ")}</th>)}</tr>
            </thead>
            <tbody>
              {anti.slice(0, 20).map((c) => (
                <tr key={c.cell.join("-")}>
                  <td>{c.expected}</td>
                  {reads(c.reads_as).map((v, i) => (
                    <td key={i} className={css.tdMuted}>{v}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>{d.occupied?.reading}</p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{tt(MORE.voidDensest)}</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>diseases</th>{axes.map((a) => <th key={a}>{a.replace(/_/g, " ")}</th>)}</tr>
            </thead>
            <tbody>
              {densest.slice(0, 8).map((c) => (
                <tr key={c.cell.join("-")}>
                  <td>{fmtInt(c.diseases)}</td>
                  {reads(c.reads_as).map((v, i) => (
                    <td key={i} className={css.tdMuted}>{v}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.note}>{d.shape?.reading}</p>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance}
                  method={d.lattice} says={d.says} limits={d.limits}
                  governedBy={d.governed_by} />
    </div>
  );
}
