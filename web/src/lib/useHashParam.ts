import { useCallback, useEffect, useState } from "react";

/** A single query parameter carried in the hash, so view state is linkable.
 *
 *  The app routes on `#view`; this appends `?key=value` after it, which keeps the router
 *  untouched and still survives a refresh, a back button and a pasted link. Filters and
 *  the active section belong here rather than in component state — anything a reader
 *  might want to send to a colleague does.
 */
export function useHashParam(key: string, fallback: string): [string, (v: string) => void] {
  const read = useCallback(() => {
    const q = window.location.hash.split("?")[1] ?? "";
    return new URLSearchParams(q).get(key) ?? fallback;
  }, [key, fallback]);

  const [value, setValue] = useState(read);

  useEffect(() => {
    const on = () => setValue(read());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, [read]);

  const set = useCallback(
    (v: string) => {
      const [view, q = ""] = window.location.hash.replace("#", "").split("?");
      const params = new URLSearchParams(q);
      if (v === fallback) params.delete(key);
      else params.set(key, v);
      const qs = params.toString();
      window.location.hash = qs ? `${view}?${qs}` : view;
      setValue(v);
    },
    [key, fallback]
  );

  return [value, set];
}
