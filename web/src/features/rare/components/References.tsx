/** The world reference map — and the bridge it was supposed to demonstrate, audited.
 *
 *  THE GAP IS THE HEADLINE, and it is not the headline the map was assembled to produce. The
 *  thesis says the unusual part of this project is the intersection of rare disease, systems
 *  biology, computational biology, HPC and compiler research. Tagging every reference with a
 *  community and a ladder rung, and then asking which communities share a rung, says the
 *  intersection is currently empty: every pair that never meets has a biological community on
 *  one side and a computational one on the other.
 *
 *  That is an honourable position — it is what a research programme looks like before it has
 *  done the joining work — and it is not the same thing as a bridge. The map is the wrong place
 *  to find that out after the thesis is written, so the finding sits above the list rather than
 *  under it.
 *
 *  PROVENANCE IS ON EVERY ROW. Claims about people, posts, programmes and money are the
 *  author's and unverified here; libraries, standards, databases and papers are common
 *  knowledge in their fields. Marking that per row rather than in a footnote is the whole
 *  point: a name attached to an institution reads as a fact whether or not anyone checked it.
 */
import { useMemo, useState } from "react";
import { references as r } from "../data/references";
import css from "./References.module.css";

type View = "bridge" | "map" | "list";

const VIEWS: { id: View; label: string; sub: string }[] = [
  { id: "bridge", label: "The bridge, audited", sub: "which communities actually meet, and where" },
  { id: "map", label: "By rung", sub: "the ladder, with who is standing on each step" },
  { id: "list", label: "Every reference", sub: "eighty-four, with provenance on each" },
];

export function References() {
  const [view, setView] = useState<View>("bridge");
  const [comm, setComm] = useState<string | null>(null);
  const s = r.summary;

  const name = useMemo(
    () => Object.fromEntries(r.communities.map((c) => [c.id, c.name])) as Record<string, string>,
    [],
  );

  const shown = useMemo(
    () => (comm ? r.references.filter((x) => x.community === comm) : r.references),
    [comm],
  );

  return (
    <div className={css.root}>
      <p className={css.premise}>{r.premise}</p>

      <div className={css.counts}>
        <Stat v={String(s.references)} l="references"
              s={`${Object.keys(s.byCommunity).length} communities, ${s.countries} countries`} />
        <Stat v={String(s.bridgedRungs)} l="rungs with more than one community"
              s="the comfortable number" />
        <Stat v={String(s.neverMeet)} l="community pairs that never share a rung"
              s="the useful one — every pair is biology against computation" hot />
        <Stat v={String(s.authorSupplied)} l="claims supplied and unverified here"
              s="people, posts, programmes and money" />
      </div>

      <nav className={css.tabs} aria-label="Reference views">
        {VIEWS.map((v) => (
          <button key={v.id} type="button" onClick={() => setView(v.id)}
                  className={v.id === view ? css.tabOn : css.tab} aria-current={v.id === view}>
            <span>{v.label}</span>
            <span className={css.tabSub}>{v.sub}</span>
          </button>
        ))}
      </nav>

      {/* ---- THE BRIDGE ----------------------------------------------------- */}
      {view === "bridge" && (
        <div className={css.bridgeWrap}>
          <section className={css.gap}>
            <span className={css.gapL}>What the map says when you ask it the right question</span>
            <p className={css.finding}>{r.finding}</p>
            <p className={css.theGap}>{r.theGap}</p>
          </section>

          <section className={css.panel}>
            <h4 className={css.h4}>Community pairs that never share a rung</h4>
            <p className={css.sub}>
              Ordered by how many references sit on each side, because a pair with forty
              references between them and no shared object is a louder silence than a pair with
              six.
            </p>
            <div className={css.neverGrid}>
              {r.neverMeet.map((p) => (
                <div key={p.a + p.b} className={css.never}>
                  <span className={css.neverA}>
                    {name[p.a]}<span className={css.neverN}>{p.refsA}</span>
                  </span>
                  <span className={css.neverX} aria-hidden="true">×</span>
                  <span className={css.neverA}>
                    {name[p.b]}<span className={css.neverN}>{p.refsB}</span>
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className={css.panel}>
            <h4 className={css.h4}>Communities confined to a single rung</h4>
            <div className={css.confined}>
              {r.confined.map((c) => (
                <div key={c.community} className={css.conf}>
                  <span className={css.confName}>{name[c.community]}</span>
                  <span className={css.confV}>{c.references} references</span>
                  <span className={css.confRung}>
                    all on <code>{c.rung}</code>
                  </span>
                  <span className={css.confShare}>
                    {c.sharesWith.length
                      ? `shared with ${c.sharesWith.map((x) => name[x]).join(", ")}`
                      : "shared with nobody"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className={css.panel}>
            <h4 className={css.h4}>Where communities do meet</h4>
            <ul className={css.pairs}>
              {r.communityPairs.map((p) => (
                <li key={p.a + p.b} className={css.pair}>
                  <span className={css.pairNames}>{name[p.a]} + {name[p.b]}</span>
                  <span className={css.pairRungs}>
                    {p.rungs.map((x) => <code key={x}>{x}</code>)}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <p className={css.formula}>{r.authorFormula}</p>
        </div>
      )}

      {/* ---- BY RUNG --------------------------------------------------------- */}
      {view === "map" && (
        <div className={css.rungs}>
          {r.bridges.filter((b) => b.references > 0).map((b) => (
            <article key={b.rung} className={b.bridged ? css.rungOk : css.rungLone}>
              <header className={css.rungHead}>
                <h4 className={css.rungName}>{b.rung}</h4>
                <span className={css.rungN}>{b.references} references</span>
                <span className={b.bridged ? css.pillOk : css.pillLone}>
                  {b.bridged ? `${b.communityCount} communities` : "one community"}
                </span>
              </header>
              <div className={css.rungComms}>
                {b.communities.map((c) => <span key={c} className={css.chip}>{name[c]}</span>)}
              </div>
              <div className={css.rungRefs}>
                {r.references.filter((x) => x.rung === b.rung).map((x) => (
                  <span key={x.id} className={css.mini} data-c={x.community}>{x.name}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}

      {/* ---- THE LIST -------------------------------------------------------- */}
      {view === "list" && (
        <div className={css.listWrap}>
          <div className={css.filters}>
            <button type="button" onClick={() => setComm(null)}
                    className={comm === null ? css.fOn : css.f}>
              all <span className={css.fN}>{r.references.length}</span>
            </button>
            {r.communities.map((c) => (
              <button key={c.id} type="button" onClick={() => setComm(c.id)}
                      className={comm === c.id ? css.fOn : css.f}>
                {c.name} <span className={css.fN}>{s.byCommunity[c.id] ?? 0}</span>
              </button>
            ))}
          </div>

          {comm && (
            <p className={css.commNote}>
              {r.communities.find((c) => c.id === comm)?.note}
              {r.communities.find((c) => c.id === comm)?.inAuthorFormula === false && (
                <> This one is carried as an influence rather than as a discipline being
                bridged, which is how the source material treats it.</>
              )}
            </p>
          )}

          <div className={css.cards}>
            {shown.map((x) => (
              <article key={x.id} className={css.card} data-c={x.community}>
                <header className={css.cardHead}>
                  <span className={css.cardName}>{x.name}</span>
                  <span className={css.kind}>{x.kind}</span>
                </header>
                <span className={css.where}>{x.where}</span>
                <p className={css.why}>{x.why}</p>
                <div className={css.meta}>
                  <span className={css.rungTag}>{x.rung}</span>
                  <span className={css.country}>{x.country}</span>
                  <span className={x.provenance === "author-supplied" ? css.provBad : css.provOk}>
                    {x.provenance === "author-supplied" ? "supplied, unverified here" : "public artifact"}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      <p className={css.provenance}>
        <strong>On provenance.</strong> {r.provenanceNote}
      </p>
    </div>
  );
}

function Stat({ v, l, s, hot }: { v: string; l: string; s: string; hot?: boolean }) {
  return (
    <div className={hot ? css.statHot : css.stat}>
      <span className={css.statV}>{v}</span>
      <span className={css.statL}>{l}</span>
      <span className={css.statS}>{s}</span>
    </div>
  );
}
