/** What is installed, what is used, and what is sitting on the machine unopened.
 *
 *  THE MIDDLE COLUMN IS THE POINT. "Installed" is trivia and "would be nice" is a wish list;
 *  INSTALLED AND UNUSED is capability already paid for and not spent, and it is the only one
 *  of the three that implies a decision. Seven libraries sit in it.
 *
 *  EVERY ROW IS A MEASUREMENT. The generator imports each module to get its real version and
 *  greps src, tools, analyses and tests to see whether this project imports it. Nothing here
 *  is a claim about intent.
 */
import { ecosystem as e } from "../../lib/data/ecosystem";

const RUNG_LABEL: Record<string, string> = {
  all: "every rung",
  genotype: "genotype",
  structure: "structure",
  dynamics: "dynamics",
  interactome: "interactome",
  pathway: "pathway",
  cell: "cell",
  tissue: "tissue",
  patient: "patient",
};

const ORDER = ["in use", "installed, unused", "not installed"] as const;
const STATUS_NOTE: Record<string, string> = {
  "in use": "imported somewhere in this repository",
  "installed, unused": "present on the machine, never imported here",
  "not installed": "would have to be added",
};

export default function Ecosystem() {
  const s = e.summary;
  return (
    <div className="eco">
      <p className="eco-premise">{e.premise}</p>

      <div className="eco-confess">
        <span className="eco-kicker">The uncomfortable part</span>
        <p>{e.confession}</p>
      </div>

      <div className="eco-stats">
        {ORDER.map((k) => (
          <div key={k} className={k === "installed, unused" ? "eco-stat hot" : "eco-stat"}>
            <span className="eco-k">{k}</span>
            <span className="eco-v num">{s.byStatus[k] ?? 0}</span>
            <span className="eco-s">{STATUS_NOTE[k]}</span>
          </div>
        ))}
        <div className="eco-stat">
          <span className="eco-k">Public resources</span>
          <span className="eco-v num">{s.resourcesIngested}/{s.resources}</span>
          <span className="eco-s">ingested; {s.resourcesNamed} named and not downloaded</span>
        </div>
      </div>

      {ORDER.map((status) => {
        const rows = e.libraries.filter((l) => l.status === status);
        if (!rows.length) return null;
        return (
          <section key={status} className="eco-group">
            <h3>
              {status}
              <span className="eco-count num">{rows.length}</span>
            </h3>
            <div className="eco-rows">
              {rows.map((l) => (
                <article key={l.module} className="eco-row" data-status={status}>
                  <div className="eco-head">
                    <span className="eco-name">{l.name}</span>
                    <span className="eco-mod num">{l.module}</span>
                    {l.version && <span className="eco-ver num">{l.version}</span>}
                    <span className="eco-rung">{RUNG_LABEL[l.rung] ?? l.rung}</span>
                  </div>
                  <p className="eco-would">{l.would}</p>
                  <p className="eco-note">{l.note}</p>
                </article>
              ))}
            </div>
          </section>
        );
      })}

      <section className="eco-group">
        <h3>
          Public resources
          <span className="eco-count num">{e.resources.length}</span>
        </h3>
        <p className="eco-sub">
          A licence is not a footnote here: Orphanet is CC BY-ND, which is why its derivatives
          stay local and are described rather than shipped. That single clause shaped the
          architecture of this project, so every candidate below carries its own.
        </p>
        <div className="eco-res">
          {e.resources.map((r) => (
            <article key={r.id} className={r.ingested ? "eco-r in" : "eco-r out"}>
              <div className="eco-head">
                <span className="eco-name">{r.name}</span>
                <span className={r.ingested ? "chip ok" : "chip bad"}>
                  {r.ingested ? "ingested" : "named, not downloaded"}
                </span>
                <span className="eco-rung">{RUNG_LABEL[r.rung] ?? r.rung}</span>
              </div>
              <p className="eco-would">{r.gives}</p>
              <p className="eco-lic">{r.licence}</p>
              <p className="eco-note">{r.note}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
