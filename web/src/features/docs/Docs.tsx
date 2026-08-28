/** Document browser over every generated finding, ADR and review in the repo.
 *
 * The documents are shipped as raw Markdown and rendered here, so the app is physically
 * incapable of drifting from the source of truth — there is no second copy to update.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { marked } from "marked";
import { docs } from "../../lib/data/docs";
import { pipeline } from "../../lib/data/pipeline";
import PipelinePanel from "./PipelinePanel";
import Ecosystem from "./Ecosystem";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { DOCS } from "../../i18n/strings";
import { useT, type Bi } from "../../i18n";
import type { Doc } from "../../lib/dataTypes";

const DOC_GROUPS: { id: Doc["group"]; label: Bi; blurb: Bi }[] = [
  { id: "method", label: DOCS.kMethod,
    blurb: { en: "The ten stages, and where else they apply.",
             pt: "Os dez estágios, e onde mais eles se aplicam." } },
  { id: "findings", label: DOCS.kFindings,
    blurb: { en: "Written by the analysis runs — never by hand.",
             pt: "Escritos pelas execuções de análise — nunca à mão." } },
  { id: "case", label: DOCS.kCase,
    blurb: { en: "The screens the method was distilled from.",
             pt: "As triagens de que o método foi destilado." } },
  { id: "adr", label: DOCS.kAdr,
    blurb: { en: "Architecture decision records.",
             pt: "Registros de decisão de arquitetura." } },
];

/** Reading time at 220 words a minute — the usual figure for technical prose, which is
 *  slower than the 250 quoted for fiction and still generous for a methods document. */
const minutes = (words: number) => Math.max(1, Math.round(words / 220));

/** The document's own headings, so a long file can be entered in the middle.
 *  Parsed from the Markdown rather than from the rendered HTML: the source is the thing that
 *  is guaranteed to exist, and it costs one pass. */
function outlineOf(body: string) {
  const out: { level: number; text: string; slug: string }[] = [];
  let fenced = false;
  for (const line of body.split("\n")) {
    if (line.startsWith("```")) { fenced = !fenced; continue; }
    if (fenced) continue;
    const m = /^(#{2,3})\s+(.+?)\s*$/.exec(line);
    if (!m) continue;
    const text = m[2].replace(/[`*_]/g, "");
    out.push({
      level: m[1].length,
      text,
      slug: text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""),
    });
  }
  return out;
}

/** The sentence a search term appears in. A hit count tells you a word is present; the
 *  sentence tells you whether it is the presence you were looking for. */
function snippetFor(body: string, q: string) {
  const at = body.toLowerCase().indexOf(q);
  if (at < 0) return null;
  const from = Math.max(0, body.lastIndexOf(".", at - 1) + 1);
  const to = body.indexOf(".", at + q.length);
  const raw = body.slice(from, to < 0 ? at + 160 : to + 1).trim();
  return raw.replace(/\s+/g, " ").slice(0, 220);
}

/* TWO LEVELS, the same as everywhere else on this site. The pipeline is not a document, so it
   does not belong in the document list; it is the other half of what "method" means. */
const EMPTY_KIND: Bi = {
  en: "Nothing here yet.",
  pt: "Nada aqui ainda.",
};

const PAGE_GROUPS: NavGroupDef[] = [
  { id: "state", label: DOCS.gState, question: DOCS.qState },
  { id: "read", label: DOCS.gRead, question: DOCS.qRead },
  { id: "tools", label: DOCS.gTools, question: DOCS.qTools },
];

/** THE FOUR KINDS OF DOCUMENT ARE SECTIONS NOW, not headings inside one scrolling list.
 *
 *  "The documents" was a single section holding every file in the repository under four
 *  sub-headings, which meant the four kinds — method, findings, case studies, decisions —
 *  were invisible from the navigation and a link to "the decisions" could not be sent. They
 *  answer different questions and carry different authority: a finding is written by a run
 *  and an ADR is written by a person. Each is now a section with its own count and its own
 *  link, and the browser filters to it. */
const SECTIONS: NavSectionDef[] = [
  { id: "stages", label: DOCS.sStages, group: "state" },
  // A kind with no files is not a section. It was rendering as a tab that led to the words
  // "nothing here yet" — a promise the repository has not made.
  ...DOC_GROUPS.filter((g) => docs.some((d) => d.group === g.id)).map((g) => ({
    id: g.id, label: g.label, group: "read",
    badge: String(docs.filter((d) => d.group === g.id).length),
  })),
  { id: "tools", label: DOCS.sTools, group: "tools" },
];

export default function Docs() {
  const t = useT();
  const { section, group } = useSectionNav({
    owner: "docs", groups: PAGE_GROUPS, sections: SECTIONS, initial: "stages",
  });
  /* The list the browser shows: the documents of the open kind, or every document that
     matches a search, because a search is a question about the corpus and not about one
     shelf of it. */
  const inKind = useMemo(() => docs.filter((d) => d.group === section), [section]);
  const [active, setActive] = useState(docs[0]?.id ?? "");
  // Opening a kind opens its first document. Leaving the previous kind's document on screen
  // under the new kind's heading would say it belonged there.
  useEffect(() => {
    if (inKind.length && !inKind.some((d) => d.id === active)) setActive(inKind[0].id);
  }, [inKind, active]);
  const [query, setQuery] = useState("");

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    return docs
      .map((d) => {
        const hits = d.body.toLowerCase().split(q).length - 1;
        return { doc: d, hits };
      })
      .filter((m) => m.hits > 0)
      .sort((a, b) => b.hits - a.hits);
  }, [query]);

  const doc = docs.find((d) => d.id === active);
  const html = useMemo(() => {
    if (!doc) return "";
    // The page renders the title itself, above the meta bar, so the document's own leading
    // H1 would print it a second time. Dropped from the SOURCE rather than hidden with CSS:
    // a heading that is present but invisible still lands in the outline and in the
    // accessibility tree, where a duplicated title is just as wrong.
    // `[^\n]*` and not `.+?`: in a JavaScript regex the dot does not match a carriage
    // return, these files are CRLF, and so the obvious pattern silently matched nothing.
    const body = doc.body.replace(/^\s*#\s+[^\n]*\r?\n/, "");
    return marked.parse(body, { async: false }) as string;
  }, [doc]);
  const outline = useMemo(() => (doc ? outlineOf(doc.body) : []), [doc]);
  const bodyRef = useRef<HTMLDivElement>(null);

  const corpus = useMemo(() => ({
    documents: docs.length,
    words: docs.reduce((n, d) => n + d.words, 0),
    groups: DOC_GROUPS.filter((g) => docs.some((d) => d.group === g.id)).length,
  }), []);

  // Anchor every rendered heading so the outline can jump to it. Done after render rather
  // than by rewriting the HTML string, so the markdown renderer stays the only thing that
  // decides what the document looks like.
  useEffect(() => {
    const root = bodyRef.current;
    if (!root) return;
    root.querySelectorAll("h2, h3").forEach((h) => {
      const text = (h.textContent ?? "").toLowerCase();
      h.id = text.replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    });
  }, [html]);

  return (
    <section className="docs-page">
      <header className="docs-hero">
        <div>
          <p className="eyebrow">Method &middot; every document in the repository</p>
          <h2>
            The documents are the repository&rsquo;s own files, rendered &mdash; not a second
            copy that can drift
          </h2>
          <p className="docs-lede">
            Findings are written by the analysis runs and never by hand, decisions are recorded
            as they are made, and the method pages say where each stage applies outside the
            screen it came from. Nothing here is authored for the website.
          </p>
        </div>
        <dl className="docs-stats">
          <div><dt>Stages</dt><dd className="num">{pipeline.summary.stages}</dd></div>
          <div>
            <dt>Stale</dt>
            <dd className={"num " + (pipeline.summary.stale ? "bad" : "ok")}>
              {pipeline.summary.stale}
            </dd>
          </div>
          <div><dt>Documents</dt><dd className="num">{corpus.documents}</dd></div>
          <div><dt>Words</dt><dd className="num">{corpus.words.toLocaleString("en-US")}</dd></div>
        </dl>
      </header>

      <SectionHeading />

      {group === "state" && <PipelinePanel />}
      {group === "tools" && <Ecosystem />}

    {group === "read" && (
    <section className="docs">
      <nav className="docs-nav card" aria-label="Documents">
        <input
          type="search"
          placeholder="Search all documents…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search all documents"
        />

        {matches ? (
          <>
            <p className="group-blurb">
              {matches.length} document{matches.length === 1 ? "" : "s"} match
            </p>
            <ul>
              {matches.map(({ doc: d, hits }) => {
                const snip = snippetFor(d.body, query.trim().toLowerCase());
                return (
                  <li key={d.id}>
                    <button
                      className={d.id === active ? "active" : ""}
                      onClick={() => setActive(d.id)}
                    >
                      <span>{d.title}</span>
                      <span className="count num">{hits}</span>
                    </button>
                    {snip && <p className="snippet">&hellip;{snip}&hellip;</p>}
                  </li>
                );
              })}
            </ul>
          </>
        ) : (
          (() => {
            const g = DOC_GROUPS.find((x) => x.id === section);
            if (!g || !inKind.length) {
              return <p className="group-blurb">{t(EMPTY_KIND)}</p>;
            }
            return (
              <section>
                <p className="group-blurb">{t(g.blurb)}</p>
                <ul>
                  {inKind.map((d) => (
                    <li key={d.id}>
                      <button
                        className={d.id === active ? "active" : ""}
                        onClick={() => setActive(d.id)}
                      >
                        <span>{d.title}</span>
                        <span className="count num">{d.words.toLocaleString("en-US")}w</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })()
        )}
      </nav>

      <article className="docs-body card">
        {doc ? (
          <>
            <div className="doc-meta">
              <span className="path num">{doc.group}/{doc.file}</span>
              <span className="num">{doc.words.toLocaleString("en-US")} words</span>
              <span className="num">{minutes(doc.words)} min read</span>
              {outline.length > 0 && <span className="num">{outline.length} sections</span>}
            </div>
            <h1 className="doc-title">{doc.title}</h1>
            <div className="prose" ref={bodyRef} dangerouslySetInnerHTML={{ __html: html }} />
          </>
        ) : (
          <p>No document selected.</p>
        )}
      </article>

      {outline.length > 2 && (
        <nav className="docs-outline card" aria-label="Sections of this document">
          <h3>On this page</h3>
          <ul>
            {outline.map((o, i) => (
              <li key={o.slug + i} className={o.level === 3 ? "sub" : ""}>
                <a href={"#" + o.slug}
                   onClick={(e) => {
                     // The app routes on the hash, so a bare anchor would change the view.
                     e.preventDefault();
                     document.getElementById(o.slug)?.scrollIntoView({ block: "start" });
                   }}>
                  {o.text}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </section>
    )}
    </section>
  );
}
