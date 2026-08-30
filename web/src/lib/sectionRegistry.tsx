import { Suspense, type ReactNode } from "react";

/** SECTIONS DECLARED AS DATA, so adding one is an entry and not an edit in four places.
 *
 *  WHY THIS EXISTS. Every measurement added to this project used to cost four touch points:
 *  an i18n block, a component, an entry in a page's `SECTIONS` array, and a branch in that
 *  page's render chain. The chains grew to 59 `section === "x" &&` branches across three
 *  pages and 1,586 lines, and the failure mode is the one this repository keeps finding
 *  elsewhere: a list and the thing it describes drift apart, silently, because nothing
 *  connects them.
 *
 *  The pipeline solved this years of commits ago — `sieve.pipeline.stages` declares every
 *  stage in one place and the runner reads it. This is the same move for the interface.
 *
 *  THE POKA-YOKE. A section in the rail with no entry here cannot render, so instead of a
 *  silently blank panel the reader gets a stated absence and the developer gets a console
 *  error naming the id. `web/scripts/check-sections.mjs` turns that into a build failure, so
 *  the drift is caught before anyone sees it rather than by someone noticing a white page.
 *
 *  WHAT A SECTION IS NOT. It is not a route and not a component. It is a heading, a
 *  sentence saying what the reader is looking at, and a view — and the sentence is not
 *  decoration in this project: it is where a figure states what it does not show.
 */

export type SectionEntry<Ctx = void> = {
  /** Matches the id in the page's nav definition. The registry is keyed on it. */
  id: string;
  /** The heading above the view. A node rather than a string because several headings
   *  carry inline emphasis, and flattening them to text would lose the emphasis that makes
   *  a sentence like "a prevalence is a property of a disorder IN A POPULATION" readable. */
  title: ReactNode | ((ctx: Ctx) => ReactNode);
  /** What the reader is looking at, and what it does not show. Required, deliberately:
   *  a figure that cannot be described in a sentence is a figure nobody can argue with. */
  sub: ReactNode | ((ctx: Ctx) => ReactNode);
  /** A section that draws its own frame. Two of the twenty-five in the rare atlas do — one
   *  opens with a warning banner, one splits into two blocks — and forcing them into the
   *  heading-plus-view shape would have meant either rewriting working views or lying about
   *  what they are. They still declare a `sub`, so the check still sees them. */
  bare?: boolean;
  /** The view itself. Takes the page's context so a section can read run state without the
   *  registry knowing what a run is. */
  view: (ctx: Ctx) => ReactNode;
};

export type SectionRegistry<Ctx = void> = readonly SectionEntry<Ctx>[];

/** Render the active section, or state plainly that it is missing.
 *
 *  The fallback is NOT a blank. A reader who followed a link to a section that no longer
 *  exists is owed the same honesty as a reader looking at a measurement: say what happened.
 */
export function renderSection<Ctx>(
  registry: SectionRegistry<Ctx>,
  id: string,
  ctx: Ctx,
  opts: { fallback?: ReactNode; className?: string; headingClass?: string; subClass?: string;
          bodyClass?: string } = {},
): ReactNode {
  const entry = registry.find((s) => s.id === id);

  if (!entry) {
    // Loud in development, graceful in production — the same split the pipeline uses when a
    // stage names an output nobody writes.
    if (import.meta.env.DEV) {
      console.error(
        `[sections] no entry for %o. Registered: %o`, id, registry.map((s) => s.id));
    }
    return (
      <section className={opts.className}>
        <div>
          <h3 className={opts.headingClass}>This section is not available</h3>
          <p className={opts.subClass}>
            The rail offers <code>{id}</code> and nothing is registered to draw it. That is a
            defect in this interface rather than a gap in the data, and
            <code> npm run check</code> fails on it.
          </p>
        </div>
      </section>
    );
  }

  if (entry.bare) {
    return (
      <Suspense key={id} fallback={opts.fallback ?? null}>
        {entry.view(ctx)}
      </Suspense>
    );
  }

  return (
    <section className={opts.className}>
      <div>
        <h3 className={opts.headingClass}>{resolve(entry.title, ctx)}</h3>
        <p className={opts.subClass}>{resolve(entry.sub, ctx)}</p>
      </div>
      <div className={opts.bodyClass}>
        <Suspense key={id} fallback={opts.fallback ?? null}>
          {entry.view(ctx)}
        </Suspense>
      </div>
    </section>
  );
}

/** A heading may be a value or a function of the context, because several of them need the
 *  page's translator and a registry is a module rather than a component — so it cannot call
 *  a hook. Passing the translator in and resolving here keeps a section a plain value that
 *  can be listed, counted and checked without being mounted. */
function resolve<Ctx>(v: ReactNode | ((ctx: Ctx) => ReactNode), ctx: Ctx): ReactNode {
  return typeof v === "function" ? (v as (c: Ctx) => ReactNode)(ctx) : v;
}

/** Every id the registry can draw. Used by the nav check and by the build-time check. */
export function registeredIds<Ctx>(registry: SectionRegistry<Ctx>): string[] {
  return registry.map((s) => s.id);
}
