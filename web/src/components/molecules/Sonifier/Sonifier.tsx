import { useEffect, useRef, useState } from "react";
import { audioAvailable, type Handle } from "../../../lib/sonify";
import css from "./Sonifier.module.css";

export type SonifierProps = {
  /** Starts the sound and returns a handle. Called only from a user gesture. */
  play: () => Handle;
  label: string;
  /** How to read the sound, in one or two sentences. Printed, never optional. */
  legend: React.ReactNode;
  onEnd?: () => void;
};

/** A play/stop control with its mapping printed beside it.
 *
 *  Audio is never started without a gesture — browsers require it, and so does anyone who
 *  has ever opened a page that made noise at them.
 */
export function Sonifier({ play, label, legend, onEnd }: SonifierProps) {
  const [on, setOn] = useState(false);
  const handle = useRef<Handle | null>(null);
  const supported = audioAvailable();

  useEffect(() => () => handle.current?.stop(), []);

  if (!supported) {
    return (
      <p className={css.unsupported}>
        Audio is unavailable in this browser — every sonification here has a visual
        equivalent above it.
      </p>
    );
  }

  const toggle = () => {
    if (on) {
      handle.current?.stop();
      handle.current = null;
      setOn(false);
      onEnd?.();
      return;
    }
    handle.current = play();
    setOn(true);
  };

  return (
    <div className={css.root}>
      <button
        type="button"
        className={`${css.button} ${on ? css.playing : ""}`}
        onClick={toggle}
        aria-pressed={on}
      >
        <span className={`${css.icon} ${on ? css.iconStop : css.iconPlay}`} aria-hidden="true" />
        {on ? "Stop" : label}
      </button>
      <p className={css.key}>{legend}</p>
    </div>
  );
}
