/** The two shard implementations must agree on every symbol.
 *
 *  A mismatch is invisible in testing and total in production: the page requests a shard that
 *  does not contain the gene and reports it missing. Python wrote the files; this asserts the
 *  TypeScript the browser runs would ask for the same ones.
 */
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { shardOf, SHARDS } from "../src/features/gene/shard.ts";

const DIR = join(import.meta.dirname, "..", "public", "data", "gene");
if (!existsSync(join(DIR, "idx.json"))) {
  console.log("shards: no gene shards on disk — skipped (run tools/gene_shards.py)");
  process.exit(0);
}

const idx = JSON.parse(readFileSync(join(DIR, "idx.json"), "utf8"));
if (idx.shards !== SHARDS) {
  console.log(`shards: FAIL — python wrote ${idx.shards} shards, TypeScript expects ${SHARDS}`);
  process.exit(1);
}

let checked = 0;
let missing = 0;
const cache = new Map();

for (const symbol of Object.keys(idx.genes)) {
  const shard = shardOf(symbol);
  if (!cache.has(shard)) {
    const f = join(DIR, `${shard}.json`);
    cache.set(shard, existsSync(f) ? JSON.parse(readFileSync(f, "utf8")) : null);
  }
  const bucket = cache.get(shard);
  if (!bucket || !(symbol in bucket)) {
    if (missing < 5) console.log(`  FAIL  ${symbol} -> shard ${shard}, not there`);
    missing++;
  }
  checked++;
}

const files = readdirSync(DIR).filter((f) => /^\d{3}\.json$/.test(f)).length;
console.log(missing
  ? `\nshards: ${missing} of ${checked} symbols resolve to the wrong shard.`
  : `shards: all ${checked.toLocaleString("en-US")} symbols resolve to their own shard `
    + `(${files} shards, python and TypeScript agree).`);
process.exit(missing ? 1 : 0);
