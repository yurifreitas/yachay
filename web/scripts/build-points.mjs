/**
 * Columnar point payload for the dense charts.
 *
 * WHY THIS EXISTS — two problems with sending entities as JSON objects.
 *
 * 1. SIZE. An array of 17,916 objects with ten named fields is ~2.5 MB of text, and
 *    every number is re-parsed from decimal on load. The same numbers as three
 *    Float32Arrays are 215 KB, and arrive ready to index.
 *
 * 2. TRUTH. `build-data.mjs` trims a long table with
 *       [...entities.slice(0, 2000), ...entities.slice(-2000)]
 *    which keeps the top and bottom of a z-sorted file and DELETES THE MIDDLE. Any
 *    scatter drawn from that is a lie: the bulk of the distribution — the part a
 *    funnel plot exists to show — is simply gone, and nothing on screen says so.
 *    Here the middle is sampled rather than dropped, and the sampling rate travels
 *    with the data so the renderer can say what it is showing.
 *
 * The output is base64 inside a JSON module (no fetch, no loader config, works from
 * file://). Base64 costs 33% over raw bytes and still beats JSON text by ~9x.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const OUT = join(REPO, "out");
const DEST = join(HERE, "..", "src", "data", "generated");

/** Points kept at full fidelity regardless of sampling — the ones a reader looks for. */
const KEEP_EXTREME = 1500;
/** Target size for the sampled bulk. Enough to render density honestly. */
const SAMPLE_BULK = 12000;

mkdirSync(DEST, { recursive: true });

function readCsv(path) {
  const text = readFileSync(path, "utf8").trim();
  if (!text) return { cols: [], rows: [] };
  const [head, ...lines] = text.split(/\r?\n/);
  const cols = head.split(",");
  return { cols, rows: lines.map((l) => l.split(",")) };
}

const b64 = (typed) => Buffer.from(typed.buffer, typed.byteOffset, typed.byteLength).toString("base64");

/**
 * Deterministic thinning that preserves density.
 *
 * Keeps every extreme (by the ranking column) and a uniform stride through the rest.
 * A stride, not a random draw, so the payload is byte-identical between builds — a
 * figure that changes when nothing changed is a figure nobody trusts.
 */
function thin(n, order) {
  if (n <= KEEP_EXTREME * 2 + SAMPLE_BULK) return { idx: order, rate: 1 };
  const keep = new Set();
  for (let i = 0; i < KEEP_EXTREME; i++) {
    keep.add(order[i]);
    keep.add(order[n - 1 - i]);
  }
  const bulk = order.slice(KEEP_EXTREME, n - KEEP_EXTREME);
  const stride = Math.ceil(bulk.length / SAMPLE_BULK);
  for (let i = 0; i < bulk.length; i += stride) keep.add(bulk[i]);
  return { idx: [...keep], rate: 1 / stride };
}

const out = {};
if (existsSync(OUT)) {
  for (const f of readdirSync(OUT)) {
    if (!f.endsWith(".manifest.json")) continue;
    const manifest = JSON.parse(readFileSync(join(OUT, f), "utf8"));
    if (!manifest.entities) continue;
    const { cols, rows } = readCsv(join(OUT, manifest.entities));
    if (!rows.length) continue;

    const col = (name) => cols.indexOf(name);
    const iEnt = col("entity");
    // Adapters differ: the DepMap run has (score, n, z); the NF2 contrast does not.
    const iScore = col("score") >= 0 ? col("score") : col("contrast_raw");
    const iN = col("n") >= 0 ? col("n") : col("n_null");
    const iZ = col("z") >= 0 ? col("z") : col("contrast_z");
    if (iScore < 0 || iN < 0 || iZ < 0) continue;

    const total = rows.length;
    const zAll = rows.map((r) => Number(r[iZ]));
    const order = [...rows.keys()].sort((a, b) => zAll[b] - zAll[a]);
    const { idx, rate } = thin(total, order);
    idx.sort((a, b) => a - b);

    const m = idx.length;
    const n = new Float32Array(m);
    const score = new Float32Array(m);
    const z = new Float32Array(m);
    const cls = new Uint8Array(m); // 0 other · 1 control · 2 confound
    const names = new Array(m);

    const iCtl = col("is_nonessential_control");
    const iEss = col("is_common_essential");
    for (let k = 0; k < m; k++) {
      const r = rows[idx[k]];
      n[k] = Number(r[iN]);
      score[k] = Number(r[iScore]);
      z[k] = Number(r[iZ]);
      names[k] = r[iEnt];
      cls[k] = iEss >= 0 && r[iEss] === "True" ? 2 : iCtl >= 0 && r[iCtl] === "True" ? 1 : 0;
    }

    out[manifest.id] = {
      total,
      shown: m,
      // The renderer prints this. A thinned chart that does not say it is thinned is
      // the same failure as the slice() it replaces.
      sampleRate: rate,
      keptExtreme: Math.min(KEEP_EXTREME, Math.floor(total / 2)),
      n: b64(n),
      score: b64(score),
      z: b64(z),
      cls: b64(cls),
      // Names dominate the payload; they are only needed on hover, so they ship as one
      // newline-joined string rather than 17,916 quoted JSON strings.
      names: names.join("\n"),
    };
    const kb = (m * 13 + names.join("\n").length) / 1024;
    console.log(
      `  points/${manifest.id}: ${m.toLocaleString('en-US')} of ${total.toLocaleString('en-US')} ` +
        `(bulk 1/${Math.round(1 / rate)}), ~${kb.toFixed(0)} KB`
    );
  }
}

writeFileSync(join(DEST, "points.json"), JSON.stringify(out));
