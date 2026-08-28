import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { NavTree } from "./types";
import type { Text } from "../../i18n";

/** The channel between a page and the shell that draws its navigation.
 *
 *  WHY A CONTEXT AND NOT PROPS. The sidebar is rendered by the shell, above the router, and
 *  the sections belong to the page, below it. Lifting the section lists into the shell would
 *  put every page's interior into the entry chunk — the exact cost the lazy routes exist to
 *  avoid — and would give the shell an opinion about what a disease is. So the page keeps its
 *  declarations, and publishes them upward for the duration of its mount.
 */

type Publish = (tree: NavTree | null, owner: string) => void;

const TreeContext = createContext<NavTree | null>(null);
const PublishContext = createContext<Publish>(() => {});

export function NavProvider({ children }: { children: ReactNode }) {
  const [tree, setTree] = useState<NavTree | null>(null);

  /** Ownership, not last-write-wins. On a route change React runs the old page's cleanup and
   *  the new page's effect, and nothing in the API guarantees which lands second. A clear
   *  that names its owner can only clear its own tree, so the sidebar cannot be emptied by
   *  the page that just left. */
  const publish = useCallback<Publish>((next, owner) => {
    setTree((cur) => {
      if (next) return next;
      return cur && cur.owner !== owner ? cur : null;
    });
  }, []);

  return (
    <PublishContext.Provider value={publish}>
      <TreeContext.Provider value={tree}>{children}</TreeContext.Provider>
    </PublishContext.Provider>
  );
}

/** Read by the sidebar. Null while no page has published — a page with no interior is a
 *  legitimate state, not a missing one. */
export function useNavTree(): NavTree | null {
  return useContext(TreeContext);
}

export function useNavPublish(): Publish {
  return useContext(PublishContext);
}

/** The current group's question and the current section's label, for a page that wants to
 *  restate above its content what the sidebar shows in the rail. */
export function useNavHeading(): { group?: Text; question?: Text; section?: Text } {
  const tree = useNavTree();
  return useMemo(() => {
    if (!tree) return {};
    const g = tree.groups.find((x) => x.id === tree.group);
    const s = tree.sections.find((x) => x.id === tree.section);
    return { group: g?.label, question: g?.question, section: s?.label };
  }, [tree]);
}
