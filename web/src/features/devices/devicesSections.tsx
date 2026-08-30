import raw from "../../data/generated/cleared_devices.json";
import type { SectionRegistry } from "../../lib/sectionRegistry";
import type { Text } from "../../i18n";
import { DEV } from "../../i18n/devices";
import { Provenance } from "../rare/components/Provenance";
import css from "../rare/components/MeasuredPanels.module.css";
import own from "./DevicesPage.module.css";

/** THE PREDICTIVE-TECHNOLOGY LAYER, and why it is counts rather than cards.
 *
 *  The obvious shape for an atlas of clinical AI is a card per technology: model, dataset,
 *  AUROC, sensitivity, regulatory status, limitations. It is a good shape and it is the one
 *  this repository may not use, because every field in it would be a number typed from a
 *  paper. ADR 0007 forbids that in one sentence — a construct enters when a tool computes it
 *  from an ingested source — and a hand-typed leaderboard would be the eleventh authored
 *  layer in a project whose one claim on the reader is traceability.
 *
 *  So the layer begins at the only rung of a readiness scale that can be OBSERVED: whether a
 *  regulator has permitted the thing. The FDA publishes that list, dated, and it is not
 *  self-reported. Everything on these screens is a count with a denominator.
 *
 *  THE FOURTH SECTION IS A CORRECTION, deliberately kept as a section rather than folded
 *  into a caveat. The tool's first version read "no dermatology panel" as "no authorised
 *  device for skin cancer" and was wrong. A site that publishes findings owes the reader its
 *  corrections at the same size as its claims.
 */

const d = raw as any;
const fmt = (n: number) => n.toLocaleString("en-US");
const pct = (v: number, p = 1) => `${(100 * v).toFixed(p)} %`;

export type DevicesCtx = { tt: (t: Text) => string };

/* ------------------------------------------------------------------ the specialties */

function Panels() {
  const rows: any[] = d.by_panel ?? [];
  const top = rows[0]?.devices || 1;
  const con = d.concentration ?? {};
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(con.largest_panel_share ?? 0)}</span>
        <p>
          <span className={css.answersK}>{con.largest_panel}</span>
          {con.reading}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>
          {fmt(d.scale?.devices ?? 0)} authorisations · {d.scale?.panels} panels ·{" "}
          {d.scale?.first_decision}–{d.scale?.last_decision}
        </span>
        {/* Bars, not a pie. The comparison is 1,164 against 9, and only a common baseline
            makes a ratio that extreme readable at all. */}
        <div className={css.rows}>
          {rows.map((r) => (
            <div key={r.panel} className={css.row}>
              <span className={css.rowLabel}>{r.panel}</span>
              <span className={css.track}>
                <span className={css.bar} style={{ width: `${(100 * r.devices) / top}%` }} />
              </span>
              <span className={css.rowVal}>{fmt(r.devices)}</span>
              <span className={css.rowNote}>{pct(r.share)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>{"what this is not"}</span>
        <p className={css.caveat}>{d.says}</p>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.not_an_adapter}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ------------------------------------------------------------------ the curve */

function Years() {
  const rows: any[] = d.by_year ?? [];
  const max = Math.max(1, ...rows.map((r) => r.devices));
  const recent = rows.filter((r) => Number(r.year) >= 2019)
    .reduce((a, r) => a + r.devices, 0);
  const total = rows.reduce((a, r) => a + r.devices, 0);
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(total ? recent / total : 0, 0)}</span>
        <p>
          <span className={css.answersK}>authorised in 2019 or later</span>
          The regulated surface of medical AI is almost entirely a thing of the last seven
          years, in a field whose literature reads as much older than that.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>authorisations by year of final decision</span>
        {/* A column per year, labelled directly. The last year is partial by construction —
            the list is a snapshot — and saying so is cheaper than a reader inferring a fall. */}
        <div className={own.cols} role="img"
             aria-label="authorisations per year, rising steeply after 2019">
          {rows.map((r) => (
            <span key={r.year} className={own.col}>
              {/* Number, then bar, then year — the column is bottom-aligned, so this puts the
                  value directly on top of the bar it labels at every height. */}
              <span className={own.colN}>{r.devices}</span>
              <span className={own.colBar} style={{ height: `${(100 * r.devices) / max}%` }} />
              <span className={own.colY}>{String(r.year).slice(2)}</span>
            </span>
          ))}
        </div>
        <p className={css.note}>
          The final year is a partial count: this list is a snapshot taken on{" "}
          <code>{d.generated}</code>, not a closed year.
        </p>
      </div>

      <Provenance generated={d.generated} provenance={d.provenance} method={d.not_an_adapter}
                  says={d.says} limits={d.limits} governedBy={d.governed_by} />
    </div>
  );
}

/* ------------------------------------------------------------------ the registered guess */

function Expected() {
  const ev = d.expected_versus_found ?? {};
  const rows: any[] = ev.rows ?? [];
  const max = Math.max(1, ...rows.map((r) => r.devices));
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>{(ev.absent ?? []).length}</span>
        <p>
          <span className={css.answersK}>expected and absent entirely</span>
          {ev.reading}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>
          written into the tool before it counted anything
        </span>
        <div className={css.rows}>
          {rows.map((r) => (
            <div key={r.panel} className={css.row}>
              <span className={css.rowLabel}>{r.panel}</span>
              <span className={css.track}>
                {r.present_in_list
                  ? <span className={css.bar} style={{ width: `${(100 * r.devices) / max}%` }} />
                  : null}
              </span>
              <span className={css.rowVal}>
                {r.present_in_list ? fmt(r.devices) : "—"}
              </span>
              <span className={css.rowNote}>
                {r.present_in_list ? "" : "panel does not appear"}
              </span>
            </div>
          ))}
        </div>
        <p className={css.note}>
          A registered expectation is what makes an absence a result. Read the correction in
          the next section before drawing anything from the dermatology row.
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ the correction */

function Correction() {
  const sk = d.skin_lesion_devices ?? {};
  const rows: any[] = sk.matched_by_name ?? [];
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={`${css.value} ${css.valueMuted}`}>{sk.count ?? 0}</span>
        <p>
          <span className={css.answersK}>skin-lesion devices, reviewed under another panel</span>
          {sk.reading}
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>found by scanning the device names, not the panels</span>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr><th>device</th><th>company</th><th>reviewed under</th><th>decided</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.submission}>
                  <td className={css.tdName}>{r.device}</td>
                  <td className={css.tdMuted}>{r.company}</td>
                  <td className={css.tdMuted}>{r.panel}</td>
                  <td className={css.tdMuted}>{r.decided}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={css.caveat}>{sk.method}</p>
        <p className={css.note}>
          Neither of these is a neural network on a photograph. MelaFind is multispectral
          imaging and DermaSensor is elastic-scattering spectroscopy — which is the argument
          for calling this area <em>predictive technologies</em> rather than clinical AI: the
          two things a regulator has permitted for skin lesions are both instruments.
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ who */

function Companies() {
  const rows: any[] = d.busiest_companies ?? [];
  const max = Math.max(1, ...rows.map((r) => r.devices));
  const held = rows.reduce((a, r) => a + r.devices, 0);
  return (
    <div className={css.wrap}>
      <div className={css.finding}>
        <span className={css.value}>{pct(held / (d.scale?.devices || 1), 0)}</span>
        <p>
          <span className={css.answersK}>held by these {rows.length} companies</span>
          A concentrated list is a statement about who can afford a regulatory pathway, which
          is a different question from who can build a model.
        </p>
      </div>

      <div className={css.block}>
        <span className={css.blockK}>
          {fmt(d.scale?.distinct_companies ?? 0)} distinct companies ·{" "}
          {fmt(d.scale?.distinct_product_codes ?? 0)} product codes
        </span>
        <div className={css.rows}>
          {rows.map((r) => (
            <div key={r.company} className={css.row}>
              <span className={css.rowLabel}>{r.company}</span>
              <span className={css.track}>
                <span className={css.bar} style={{ width: `${(100 * r.devices) / max}%` }} />
              </span>
              <span className={css.rowVal}>{fmt(r.devices)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ registry */

export const DEVICE_SECTIONS: SectionRegistry<DevicesCtx> = [
  {
    id: "panels",
    title: (ctx) => (<>{ctx.tt(DEV.panelHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEV.panelSub)}</>),
    view: () => (<><Panels /></>),
  },
  {
    id: "years",
    title: (ctx) => (<>{ctx.tt(DEV.yearHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEV.yearSub)}</>),
    view: () => (<><Years /></>),
  },
  {
    id: "companies",
    title: (ctx) => (<>{ctx.tt(DEV.whoHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEV.whoSub)}</>),
    view: () => (<><Companies /></>),
  },
  {
    id: "expected",
    title: (ctx) => (<>{ctx.tt(DEV.expHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEV.expSub)}</>),
    view: () => (<><Expected /></>),
  },
  {
    id: "correction",
    title: (ctx) => (<>{ctx.tt(DEV.skinHeading)}</>),
    sub: (ctx) => (<>{ctx.tt(DEV.skinSub)}</>),
    view: () => (<><Correction /></>),
  },
];
