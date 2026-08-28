/** Which shard a gene symbol lives in.
 *
 *  THE OTHER HALF OF `tools/gene_shards.py`. Two implementations of one rule is two chances
 *  for them to disagree, and a disagreement here is silent: the browser asks for shard 041,
 *  the gene is in 093, and the page says "not found" for a gene that is right there.
 *
 *  So the rule is chosen to be trivially identical in both languages — FNV-1a, 32-bit, eight
 *  lines — and `scripts/check-shards.mjs` asserts the two agree on every symbol in the index,
 *  in the build, beside the other gates.
 */
export const SHARDS = 128;

export function shardOf(symbol: string): string {
  let h = 0x811c9dc5;
  // UTF-8 bytes, not code units: the Python side hashes bytes, and a symbol outside ASCII
  // would otherwise land in a different bucket in each language.
  for (const byte of new TextEncoder().encode(symbol)) {
    h ^= byte;
    // Multiply in 32-bit unsigned arithmetic. `Math.imul` is the only way to do this in
    // JavaScript without the result silently losing precision above 2^53.
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return String(h % SHARDS).padStart(3, "0");
}
