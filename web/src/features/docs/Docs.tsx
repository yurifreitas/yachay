/** Document browser over every generated finding, ADR and review in the repo.
 *
 * The documents are shipped as raw Markdown and rendered here, so the app is physically
 * incapable of drifting from the source of truth — there is no second copy to update.
 */
import { useMemo, useState } from "react";
import { marked } from "marked";
import { docs, type Doc } from "../../lib/data";

const GROUPS: { id: Doc["group"]; label: string; blurb: string }[] = [
  { id: "method", label: "Method", blurb: "The ten stages, and where else they apply." },
  { id: "findings", label: "Findings", blurb: "Written by the analysis runs — never by hand." },
  { id: "case", label: "Case studies", blurb: "The screens the method was distilled from." },
  { id: "adr", label: "Decisions", blurb: "Architecture decision records." },
];

export default function Docs() {
  const [active, setActive] = useState(docs[0]?.id ?? "");
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
  const html = useMemo(
    () => (doc ? (marked.parse(doc.body, { async: false }) as string) : ""),
    [doc]
  );

  return (
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
              {matches.map(({ doc: d, hits }) => (
                <li key={d.id}>
                  <button
                    className={d.id === active ? "active" : ""}
                    onClick={() => setActive(d.id)}
                  >
                    <span>{d.title}</span>
                    <span className="count num">{hits}</span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : (
          GROUPS.map((g) => {
            const items = docs.filter((d) => d.group === g.id);
            if (!items.length) return null;
            return (
              <section key={g.id}>
                <h3>{g.label}</h3>
                <p className="group-blurb">{g.blurb}</p>
                <ul>
                  {items.map((d) => (
                    <li key={d.id}>
                      <button
                        className={d.id === active ? "active" : ""}
                        onClick={() => setActive(d.id)}
                      >
                        <span>{d.title}</span>
                        <span className="count num">{d.words.toLocaleString()}w</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })
        )}
      </nav>

      <article className="docs-body card">
        {doc ? (
          <>
            <p className="path num">{doc.group}/{doc.file}</p>
            <div className="prose" dangerouslySetInnerHTML={{ __html: html }} />
          </>
        ) : (
          <p>No document selected.</p>
        )}
      </article>
    </section>
  );
}
