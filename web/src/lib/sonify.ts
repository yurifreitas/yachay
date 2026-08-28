/** Sonification engine — Web Audio, no dependency, no autoplay.
 *
 *  WHEN SOUND BEATS SIGHT, and it is a narrow list:
 *
 *  1. DEVIATION FROM A REFERENCE. Two tones a fraction of a semitone apart produce an
 *     audible *beat* — a slow throb whose rate is the frequency difference. The ear
 *     resolves this far below the threshold at which the eye separates two nearly
 *     coincident points on a diagonal. A Q-Q plot near the reference line is exactly that
 *     situation: the departure that matters most is the one hardest to see.
 *
 *  2. SERIAL COMPARISON. Seven distributions take seven fixations to read and one sweep to
 *     hear.
 *
 *  3. ACCESSIBILITY. A reader who cannot see the Q-Q plot gets nothing from it. Here sound
 *     is not an enrichment, it is the only channel.
 *
 *  RULES THIS FILE ENFORCES
 *  - Never autoplay. Every sound is user-initiated; `AudioContext` is created on the first
 *    gesture, which is also what browsers require.
 *  - Always stoppable, and always stops itself.
 *  - The mapping is printed next to the control. A sonification nobody can read the key to
 *    is a novelty, not a channel.
 *  - Amplitude is enveloped. Square-edged gain changes click, and a click reads as data.
 */

let ctx: AudioContext | null = null;

/** Created lazily inside a user gesture — browsers refuse otherwise, and so do we. */
function audio(): AudioContext {
  ctx ??= new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
  if (ctx.state === "suspended") void ctx.resume();
  return ctx;
}

export function audioAvailable(): boolean {
  return typeof window !== "undefined" && "AudioContext" in window;
}

/** Map a value onto pitch. Log in frequency, because pitch perception is logarithmic:
 *  equal ratios sound like equal steps, equal differences do not. */
function pitch(v: number, lo: number, hi: number, fLo = 196, fHi = 1568): number {
  const t = hi === lo ? 0.5 : Math.min(1, Math.max(0, (v - lo) / (hi - lo)));
  return fLo * Math.pow(fHi / fLo, t);
}

export type Handle = { stop: () => void };

/**
 * "Is the null in tune?" — the Q-Q plot as an interval.
 *
 * Two voices sweep the quantiles together: one at the pitch a correct null would give
 * (the theoretical quantile), one at the pitch actually observed. Perfect calibration is
 * a **unison** — the two collapse into one tone. Any departure opens an interval, and the
 * ear hears the beating before the eye separates the points.
 *
 * Read aloud: *a correct null sounds like one note; a wrong one sounds like two.*
 */
export function playQQ(
  theoretical: number[],
  observed: number[],
  opts: { seconds?: number; onProgress?: (i: number) => void } = {}
): Handle {
  const ac = audio();
  const seconds = opts.seconds ?? 6;
  const n = Math.min(theoretical.length, observed.length);
  const all = [...theoretical, ...observed];
  const lo = Math.min(...all);
  const hi = Math.max(...all);

  const master = ac.createGain();
  master.gain.value = 0.0001;
  master.connect(ac.destination);
  master.gain.exponentialRampToValueAtTime(0.16, ac.currentTime + 0.08);

  const ref = ac.createOscillator();
  ref.type = "sine";
  const obs = ac.createOscillator();
  obs.type = "sine";

  // The observed voice is detuned in timbre, not just pitch, so the two remain separable
  // when they are far apart and fuse cleanly when they coincide.
  const obsGain = ac.createGain();
  obsGain.gain.value = 0.85;
  ref.connect(master);
  obs.connect(obsGain);
  obsGain.connect(master);

  const t0 = ac.currentTime + 0.05;
  const step = seconds / n;
  for (let i = 0; i < n; i++) {
    const t = t0 + i * step;
    ref.frequency.setValueAtTime(pitch(theoretical[i], lo, hi), t);
    obs.frequency.setValueAtTime(pitch(observed[i], lo, hi), t);
  }
  ref.start(t0);
  obs.start(t0);

  let raf = 0;
  if (opts.onProgress) {
    const tick = () => {
      const i = Math.floor(((ac.currentTime - t0) / seconds) * n);
      if (i >= 0 && i < n) opts.onProgress!(i);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
  }

  const stop = () => {
    cancelAnimationFrame(raf);
    const t = ac.currentTime;
    master.gain.cancelScheduledValues(t);
    master.gain.setValueAtTime(Math.max(master.gain.value, 0.0001), t);
    master.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
    ref.stop(t + 0.16);
    obs.stop(t + 0.16);
    opts.onProgress?.(-1);
  };
  ref.onended = () => opts.onProgress?.(-1);
  setTimeout(stop, (seconds + 0.3) * 1000);
  return { stop };
}

/**
 * "How much do we actually know?" — uncertainty as timbre.
 *
 * The estimate is a pitch; the *interval around it* is bandwidth. A narrow interval is a
 * pure tone. A wide one is a band of noise centred on the same pitch — you can still tell
 * roughly where it sits, and you cannot tell exactly, which is the point.
 *
 * This mapping is literal rather than clever: uncertainty sounds uncertain. That is why it
 * needs no training to read, which is the usual objection to sonification.
 */
export function playUncertainty(
  p: number,
  lo: number,
  hi: number,
  opts: { seconds?: number } = {}
): Handle {
  const ac = audio();
  const seconds = opts.seconds ?? 2.2;
  const centre = pitch(p, 0, 1, 220, 1320);
  const width = Math.min(1, Math.max(0, hi - lo));

  const master = ac.createGain();
  master.gain.value = 0.0001;
  master.connect(ac.destination);

  // Tone: what we think the value is.
  const tone = ac.createOscillator();
  tone.type = "sine";
  tone.frequency.value = centre;
  const toneGain = ac.createGain();
  toneGain.gain.value = 0.5 * (1 - width * 0.75);
  tone.connect(toneGain);
  toneGain.connect(master);

  // Noise band: how much room the interval leaves. Q falls as the interval widens, so a
  // wide interval is a broad, unpitched hiss and a narrow one is nearly the tone itself.
  const len = Math.ceil(ac.sampleRate * seconds);
  const buf = ac.createBuffer(1, len, ac.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
  const noise = ac.createBufferSource();
  noise.buffer = buf;
  const band = ac.createBiquadFilter();
  band.type = "bandpass";
  band.frequency.value = centre;
  band.Q.value = Math.max(0.6, 22 * (1 - width));
  const noiseGain = ac.createGain();
  noiseGain.gain.value = 0.05 + width * 0.5;
  noise.connect(band);
  band.connect(noiseGain);
  noiseGain.connect(master);

  const t = ac.currentTime + 0.02;
  master.gain.exponentialRampToValueAtTime(0.22, t + 0.05);
  master.gain.exponentialRampToValueAtTime(0.0001, t + seconds);
  tone.start(t);
  noise.start(t);
  tone.stop(t + seconds + 0.05);
  noise.stop(t + seconds + 0.05);

  return {
    stop: () => {
      const now = ac.currentTime;
      master.gain.cancelScheduledValues(now);
      master.gain.setValueAtTime(Math.max(master.gain.value, 0.0001), now);
      master.gain.exponentialRampToValueAtTime(0.0001, now + 0.1);
      tone.stop(now + 0.14);
      noise.stop(now + 0.14);
    },
  };
}
