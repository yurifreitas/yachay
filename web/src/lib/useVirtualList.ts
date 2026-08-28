/** Windowed rendering for a long, uniform list.
 *
 *  WHY THIS EXISTS RATHER THAN A DEPENDENCY. The list it was written for is 386 rows today
 *  and the payload it reads from covers 6,728 disorders — so the honest range is "hundreds
 *  now, thousands when the next source lands". A fixed-height window is about forty lines
 *  and has no failure mode the reader cannot see; a virtualisation library is a dependency,
 *  a bundle, and an API to learn, and the app's own standard is one library per job.
 *
 *  THE DESIGN CONSTRAINT THAT MAKES IT SIMPLE. Rows are a fixed height and expansion opens a
 *  detail panel BESIDE the list rather than inside it. That is not a concession to the
 *  implementation — an inline expander at this length is worse to use, because it moves
 *  every row below it and loses the reader's place. Fixed height falls out of the right
 *  interaction rather than dictating it.
 *
 *  WHAT IT DELIBERATELY DOES NOT DO. No smooth-scroll animation (it fights the scrollbar),
 *  no scroll-anchoring heuristics (the container owns its scroll), and no measurement of
 *  real row heights — if a row ever needs to be taller, the height constant changes here,
 *  in one place, and the CSS reads it from the same source.
 */
import { useCallback, useEffect, useRef, useState } from "react";

export type VirtualWindow = {
  /** Attach to the scrolling element. */
  ref: React.RefObject<HTMLDivElement>;
  /** Total height of the scrollable content, so the scrollbar is honest. */
  totalHeight: number;
  /** Index of the first rendered row, and the pixel offset it must be pushed down by. */
  start: number;
  end: number;
  offsetY: number;
  /** Bring a row into view — used by keyboard navigation, which must never select a row
   *  the reader cannot see. */
  scrollToIndex: (index: number) => void;
};

export function useVirtualList(
  count: number,
  rowHeight: number,
  viewportHeight: number,
  overscan = 6
): VirtualWindow {
  const ref = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Passive: this listener never calls preventDefault, and saying so lets the browser
    // keep scrolling off the main thread.
    const onScroll = () => setScrollTop(el.scrollTop);
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  // A filter that shortens the list can leave the container scrolled past the new end,
  // which renders an empty window over a list that has results. Reset to the top when the
  // count changes — the same thing a reader expects after typing in a search box.
  useEffect(() => {
    const el = ref.current;
    if (el && el.scrollTop > 0) {
      el.scrollTop = 0;
      setScrollTop(0);
    }
  }, [count]);

  const start = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const visible = Math.ceil(viewportHeight / rowHeight) + overscan * 2;
  const end = Math.min(count, start + visible);

  const scrollToIndex = useCallback(
    (index: number) => {
      const el = ref.current;
      if (!el) return;
      const top = index * rowHeight;
      const bottom = top + rowHeight;
      if (top < el.scrollTop) el.scrollTop = top;
      else if (bottom > el.scrollTop + viewportHeight) el.scrollTop = bottom - viewportHeight;
    },
    [rowHeight, viewportHeight]
  );

  return { ref, totalHeight: count * rowHeight, start, end, offsetY: start * rowHeight, scrollToIndex };
}
