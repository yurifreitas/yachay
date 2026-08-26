/** Tiny scale helpers — enough for the handful of charts here, no chart library. */

export type Scale = ((v: number) => number) & { domain: [number, number]; ticks(n?: number): number[] };

function make(fwd: (v: number) => number, domain: [number, number], tick: (n: number) => number[]): Scale {
  const s = fwd as Scale;
  s.domain = domain;
  s.ticks = (n = 5) => tick(n);
  return s;
}

export function linear(domain: [number, number], range: [number, number]): Scale {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  return make(
    (v) => r0 + ((v - d0) / span) * (r1 - r0),
    domain,
    (n) => {
      const step = niceStep(span / n);
      const out: number[] = [];
      for (let t = Math.ceil(d0 / step) * step; t <= d1 + 1e-9; t += step) out.push(round(t));
      return out;
    }
  );
}

export function log(domain: [number, number], range: [number, number]): Scale {
  const [d0, d1] = domain.map((v) => Math.log10(Math.max(v, 1e-9))) as [number, number];
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  return make(
    (v) => r0 + ((Math.log10(Math.max(v, 1e-9)) - d0) / span) * (r1 - r0),
    domain,
    () => {
      const out: number[] = [];
      for (let e = Math.floor(d0); e <= Math.ceil(d1); e++) {
        for (const m of [1, 2, 5]) {
          const t = m * 10 ** e;
          if (t >= domain[0] && t <= domain[1]) out.push(t);
        }
      }
      return out;
    }
  );
}

function niceStep(raw: number): number {
  const e = 10 ** Math.floor(Math.log10(Math.abs(raw) || 1));
  const f = raw / e;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * e;
}

const round = (v: number) => Number(v.toPrecision(12));

export const fmt = (v: number, d = 2) =>
  v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

export const fmtInt = (v: number) => v.toLocaleString("en-US");

export const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;
