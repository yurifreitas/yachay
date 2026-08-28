import { useEffect, useRef, useState } from "react";

/** Fetch a generated dataset that is too large to live in the JavaScript bundle.
 *
 *  WHY THIS EXISTS. A JSON module import is parsed before the component that needs it can
 *  render, and it counts against the parse budget of every route that touches its chunk. Past
 *  a few hundred kilobytes that is the wrong trade: the data is not needed to paint the page,
 *  only to fill one panel. Fetching it puts the cost after first paint and lets the browser
 *  cache it as an ordinary asset.
 *
 *  The four states are all real and all rendered by the caller: loading, error, empty and
 *  ready. An asset can 404 after a bad deploy, and a spinner that never resolves is the worst
 *  of the four outcomes to ship.
 */
export type Remote<T> =
  | { state: "loading" }
  | { state: "error"; message: string }
  | { state: "ready"; data: T; stale?: boolean };

/** `keepPrevious` keeps the last successful payload on screen while a NEW url loads, marking
 *  it `stale`. Opt-in, because it is only right when the two payloads answer the same
 *  question at a different setting.
 *
 *  WHY IT EXISTS. The cancer section keys its fetch on the subgroup level, so changing level
 *  returned `loading` and the page rendered a skeleton — **unmounting everything**, including
 *  the control the reader had just operated. Focus went to the document root and scroll
 *  position was lost, so a keyboard user could change the level exactly once and then had
 *  nothing to press. A filter that destroys the page it filters is not a filter. */

const cache = new Map<string, unknown>();

export function useRemoteData<T>(
  url: string,
  opts: { keepPrevious?: boolean } = {},
): Remote<T> {
  const [result, setResult] = useState<Remote<T>>(() =>
    cache.has(url) ? { state: "ready", data: cache.get(url) as T } : { state: "loading" });
  // Held across url changes, so the previous answer can stay on screen. A ref rather than
  // state: it must not itself trigger a render.
  const last = useRef<T | undefined>(undefined);
  if (result.state === "ready") last.current = result.data;

  useEffect(() => {
    if (cache.has(url)) {
      setResult({ state: "ready", data: cache.get(url) as T });
      return;
    }
    let live = true;
    setResult(opts.keepPrevious && last.current !== undefined
      ? { state: "ready", data: last.current, stale: true }
      : { state: "loading" });
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
      })
      .then((data) => {
        cache.set(url, data);
        if (live) setResult({ state: "ready", data: data as T });
      })
      .catch((e: unknown) => {
        if (live) {
          setResult({
            state: "error",
            message: e instanceof Error ? e.message : "could not load",
          });
        }
      });
    return () => { live = false; };
  }, [url]);

  return result;
}

/** Where the fetched datasets live. Kept in one place so the build script and the loader
 *  cannot drift apart silently. */
export const DATA_URL = (name: string) => `${import.meta.env.BASE_URL}data/${name}.json`;
