"""Split the gene join into shards the browser can fetch one of.

THE PROBLEM THIS SOLVES. `gene_index.json` and `gene_world.json` are 5.7 MB and 14.4 MB. A
reader who opens the navigator to look up one symbol should not download twenty megabytes to
read forty numbers, and on a phone on a clinic's wifi they will not: they will close the tab.

Static hosting has no query interface, so the choice is between one enormous file and many
small ones. Many small ones, addressed by a stable rule:

    data/gene/idx.json        every symbol, plus how many layers describe it — for the search
    data/gene/<shard>.json    the full record for every symbol in that shard

The shard is a hash of the symbol, not its first letter. First-letter buckets are wildly
uneven in gene nomenclature — everything beginning with C, S and Z against almost nothing
beginning with X — and an uneven shard is the same download problem in a smaller coat.

`idx.json` is the only file loaded up front, and it is deliberately thin: a symbol and one
integer. That is what the search needs, and nothing else has to arrive before someone types.

Run after `gene_index.py` and `gene_world.py`:  `python tools/gene_shards.py`
"""

from __future__ import annotations

import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DEST = ROOT / "web" / "public" / "data" / "gene"

# 128 shards puts roughly 140 genes in each: a few tens of kilobytes, one round trip, and few
# enough files that a directory listing is still readable by a person.
SHARDS = 128


def shard_of(symbol: str) -> str:
    """FNV-1a, 32-bit. Stable across runs, machines and languages.

    Python's own `hash()` is salted per process, so a shard computed here would not match one
    computed tomorrow. A cryptographic digest would be stable but the browser has no MD5 and
    Web Crypto is async, which would put an await in front of every lookup.

    FNV-1a is eight lines in both languages and produces the same integer in both — which is
    the only property that matters here. `web/src/features/gene/shard.ts` is the other half,
    and a test asserts the two agree.
    """
    h = 0x811C9DC5
    for byte in symbol.encode("utf-8"):
        h ^= byte
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h % SHARDS:03d}"


def main() -> int:
    index_path = OUT / "gene_index.json"
    world_path = OUT / "gene_world.json"
    if not index_path.exists():
        print("out/gene_index.json absent — run tools/gene_index.py first")
        return 1

    geo_path = OUT / "gene_geometry.json"
    dom_path = OUT / "gene_domains.json"
    rel_path = OUT / "gene_related.json"

    def _load(path, label):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        print(f"  ({label} absent — shards will omit it)")
        return {"genes": {}, "scope": {}, "generated": "", "premise": "", "caution": ""}

    index = json.loads(index_path.read_text(encoding="utf-8"))
    world = _load(world_path, "gene_world.json")
    geo = _load(geo_path, "gene_geometry.json")
    dom = _load(dom_path, "gene_domains.json")
    rel = _load(rel_path, "gene_related.json")

    symbols = sorted(
        set(index["genes"]) | set(world["genes"]) | set(geo["genes"]) | set(dom["genes"]))

    if DEST.exists():
        # Rebuilt from scratch: a stale shard from a previous run is a gene whose record
        # silently disagrees with the index, which is worse than a missing one.
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True, exist_ok=True)

    buckets: dict[str, dict] = {}
    thin: dict[str, int] = {}

    for sym in symbols:
        rec = dict(index["genes"].get(sym, {}))
        w = world["genes"].get(sym)
        if w:
            rec["world"] = w
        g = geo["genes"].get(sym)
        if g:
            rec["geo"] = g
        d = dom["genes"].get(sym)
        if d:
            rec["dom"] = d
        r = rel["genes"].get(sym)
        if r:
            rec["rel"] = r
        buckets.setdefault(shard_of(sym), {})[sym] = rec

        # The search payload: how many of the six layers say anything. One integer per gene,
        # so a 18,000-symbol search index stays under a megabyte.
        layers = sum([
            "dep" in rec, bool(rec.get("cancer")), bool(rec.get("genotype")),
            "net" in rec, bool(rec.get("dis")), bool(w), bool(g),
        ])
        thin[sym] = layers

    for shard, genes in buckets.items():
        (DEST / f"{shard}.json").write_text(
            json.dumps(genes, separators=(",", ":")), encoding="utf-8")

    (DEST / "idx.json").write_text(json.dumps({
        "generated": "tools/gene_shards.py",
        "shards": SHARDS,
        "scope": {**index.get("scope", {}), "world": world.get("scope", {}),
                  "geo": geo.get("scope", {}), "dom": dom.get("scope", {}),
                  "rel": rel.get("scope", {})},
        "premise": index.get("premise", ""),
        "worldPremise": world.get("premise", ""),
        "geoCaution": geo.get("caution", ""),
        "domCaution": dom.get("caution", ""),
        "domKinds": dom.get("kinds", {}),
        "relRoutes": rel.get("routes", {}),
        "genes": thin,
    }, separators=(",", ":")), encoding="utf-8")

    sizes = sorted((DEST / f"{s}.json").stat().st_size for s in buckets)
    idx_kb = (DEST / "idx.json").stat().st_size / 1024
    total = sum(sizes) / 1024 / 1024
    print(f"{len(symbols):,} genes over {len(buckets)} shards")
    print(f"  search index   {idx_kb:,.0f} kB   (the only file loaded up front)")
    print(f"  shard median   {sizes[len(sizes) // 2] / 1024:,.0f} kB")
    print(f"  shard largest  {sizes[-1] / 1024:,.0f} kB")
    print(f"  total on disk  {total:,.1f} MB")
    print(f"wrote {DEST.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
