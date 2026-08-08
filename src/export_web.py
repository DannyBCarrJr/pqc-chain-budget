#!/usr/bin/env python3
"""Export the checker's static data for carrdigital.dev (no backend, no drift).

Emits:
  out/meta.json      corpus provenance, constants, assumptions, aggregate table
  out/shards/XX.json two-char-prefix shards; each domain row carries measured
                     facts plus all eight precomputed scenario flights, so the
                     page only compares integers against the selected window.

Every projected figure inherits the Proposed stamp and assumption set from
project_chains.py; meta.json restates both so the page can display them.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import product
from pathlib import Path

from project_chains import MLDSA, NON_CV_OVERHEAD, SCT_CLASSICAL_SIG, WINDOWS, project_domain

SCENARIOS = list(product(("ML-DSA-44", "ML-DSA-65"), ("classical", "migrated"), ("full", "leaf-only")))


def shard_key(domain: str) -> str:
    s = "".join(c if c.isalnum() else "_" for c in domain.lower()[:2])
    return (s + "__")[:2]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="summary JSONL from parse_chains.py")
    ap.add_argument("--out", required=True, type=Path, help="output directory")
    ap.add_argument("--tranco-meta", type=Path, default=Path("data/tranco-list-meta.json"))
    args = ap.parse_args()

    recs = [json.loads(l) for l in args.input.open() if '"_meta"' not in l[:12]]
    ok = [r for r in recs if r.get("ok") and r.get("certs") and not any("parse_error" in c for c in r["certs"])]

    shards: dict[str, dict[str, list]] = defaultdict(dict)
    agg = {f"{p}|{s}|{m}": [] for p, s, m in SCENARIOS}
    for r in ok:
        flights = []
        skip = False
        for p, s, m in SCENARIOS:
            proj = project_domain(r, p, s, m)
            if proj is None:
                skip = True
                break
            flights.append(proj["projected_flight"])
            agg[f"{p}|{s}|{m}"].append(proj["projected_flight"])
        if skip:
            continue
        leaf = r["certs"][0]
        shards[shard_key(r["domain"])][r["domain"]] = [
            r.get("rank"),
            r["total_der_bytes"],
            r["depth"],
            leaf.get("sct_count", 0),
            1 if r["root_transmitted"] else 0,
            leaf.get("pubkey_alg", "?").split("-")[0],
            flights,
        ]

    shard_dir = args.out / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    for key, rows in shards.items():
        (shard_dir / f"{key}.json").write_text(json.dumps(rows, separators=(",", ":")))

    table = {}
    for k, fl in agg.items():
        fl.sort()
        n = len(fl)
        table[k] = {
            "p50": fl[n // 2],
            "p95": fl[int(0.95 * n)],
            "over_iw10_pct": round(sum(1 for f in fl if f > WINDOWS["IW10"]) / n * 100, 1),
            "over_iw20_pct": round(sum(1 for f in fl if f > WINDOWS["IW20"]) / n * 100, 1),
        }

    tranco = json.loads(args.tranco_meta.read_text())
    meta = {
        "generated": "2026-08-07",
        "stamp": "Proposed",
        "corpus": {
            "tranco_list_id": tranco["list_id"],
            "tranco_created": tranco["created_on"],
            "domains_attempted": 10000,
            "chains_captured": len(ok),
        },
        "row_fields": ["rank", "classical_chain_der", "depth", "leaf_sct_count", "root_transmitted", "leaf_key_alg", "scenario_flights"],
        "scenarios": [f"{p}|{s}|{m}" for p, s, m in SCENARIOS],
        "windows": WINDOWS,
        "constants": {"mldsa": MLDSA, "non_cv_overhead": NON_CV_OVERHEAD, "sct_classical_sig": SCT_CLASSICAL_SIG},
        "assumptions": [
            "Projection swaps only measured signature and SPKI bytes for FIPS 204 sizes; DNs, SANs, extensions and SCT structure keep their measured size.",
            "Chain depth and root transmission stay exactly as observed at capture time.",
            "Each embedded SCT today carries a ~71-byte ECDSA signature.",
            "Flight = projected chain + Certificate framing (12 + 5/cert) + CertificateVerify (signature + 4) + 1,256 bytes measured non-CV overhead (pqc-cert-matrix, one lab stack).",
            "Real servers may run initcwnd above IW10; the window is selectable for that reason.",
        ],
        "aggregate": table,
    }
    (args.out / "meta.json").write_text(json.dumps(meta, indent=1))

    sizes = sorted(p.stat().st_size for p in shard_dir.glob("*.json"))
    total = sum(sizes)
    print(f"exported {sum(len(v) for v in shards.values())} domains into {len(sizes)} shards")
    print(f"shard bytes: min={sizes[0]} median={sizes[len(sizes)//2]} max={sizes[-1]} total={total/1024:.0f}KB")
    print(f"meta.json: {(args.out / 'meta.json').stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
