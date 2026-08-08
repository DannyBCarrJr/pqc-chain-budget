#!/usr/bin/env python3
"""Corpus-level statistics from a parsed summary (parse_chains.py output).

Prints the Phase 1 sanity block: success rate, served-chain size percentiles
against published baselines, depth and ICA distributions, root transmission,
leaf key algorithms, SCT and SAN distributions, fixed-depth size spread, and
the failure taxonomy. Every baseline cited here is Reported (see PRIOR-ART.md);
every computed number is Verified against the capture evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Reported baselines, cited for comparison only (see PRIOR-ART.md).
CERT_ABRIDGE_P5_P50_P95 = (2308, 4032, 5609)  # draft-ietf-tls-cert-abridge-02, ~75k Tranco chains
SIKERIDIS_ICA = "0 ICA 13-31%, 1 ICA 35-45%, 2 ICA 24-30%, 3 ICA 9-12%"  # ePrint 2022/1556, Tranco 10k 2022
LONGITUDINAL_LEAF = "RSA 56.9% / ECDSA 43.1%"  # arXiv:2607.29005


def pctile(sorted_vals: list[int], p: float) -> int:
    return sorted_vals[min(len(sorted_vals) - 1, int(p / 100 * len(sorted_vals)))]


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.open() if '"_meta"' not in l[:12]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="summary JSONL from parse_chains.py")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of text")
    args = ap.parse_args()

    recs = load(args.input)
    ok = [r for r in recs if r.get("ok")]
    n = len(ok)
    if not n:
        print("no successful captures in input", file=sys.stderr)
        return 1

    sizes = sorted(r["total_der_bytes"] for r in ok)
    depth = Counter(r["depth"] for r in ok)
    # Floor at 0: a served self-signed single cert is leaf and root in one,
    # not a negative intermediate count.
    ica = Counter(max(0, r["depth"] - 1 - (1 if r["root_transmitted"] else 0)) for r in ok)
    root_tx = sum(1 for r in ok if r["root_transmitted"])
    leaf_key = Counter(r["certs"][0].get("pubkey_alg", "?").split("-")[0] for r in ok if r["certs"])
    scts = Counter(r["certs"][0].get("sct_count", 0) for r in ok if r["certs"])
    sans = sorted(r["certs"][0].get("san_count", 0) for r in ok if r["certs"])
    fails = Counter((r.get("error") or "?").split(":")[0] for r in recs if not r.get("ok"))
    parse_errors = sum(1 for r in ok for c in r["certs"] if "parse_error" in c)

    spread: dict[int, dict[str, float | int]] = {}
    for d in sorted(depth):
        ss = sorted(r["total_der_bytes"] for r in ok if r["depth"] == d)
        if len(ss) >= 30:
            p5, p50, p95 = pctile(ss, 5), pctile(ss, 50), pctile(ss, 95)
            spread[d] = {"n": len(ss), "p5": p5, "p50": p50, "p95": p95, "p95_over_p5": round(p95 / p5, 2)}

    stats: dict[str, Any] = {
        "records": len(recs),
        "ok": n,
        "success_rate_pct": round(n / len(recs) * 100, 1),
        "chain_bytes": {"p5": pctile(sizes, 5), "p50": pctile(sizes, 50), "p95": pctile(sizes, 95), "max": sizes[-1]},
        "depth": dict(sorted(depth.items())),
        "ica": {k: {"n": v, "pct": round(v / n * 100, 1)} for k, v in sorted(ica.items())},
        "root_transmitted": {"n": root_tx, "pct": round(root_tx / n * 100, 1)},
        "leaf_key_alg": {k: {"n": v, "pct": round(v / n * 100, 1)} for k, v in leaf_key.most_common()},
        "leaf_sct_count": dict(sorted(scts.items())),
        "leaf_san": {"p50": pctile(sans, 50), "p95": pctile(sans, 95), "max": sans[-1]},
        "size_spread_by_depth": spread,
        "failures": dict(fails.most_common()),
        "cert_parse_errors": parse_errors,
    }

    if args.json:
        print(json.dumps(stats, indent=2))
        return 0

    c = stats["chain_bytes"]
    print(f"records={stats['records']} ok={n} ({stats['success_rate_pct']}% success)")
    print(f"\nserved chain bytes: p5={c['p5']} p50={c['p50']} p95={c['p95']} max={c['max']}")
    print(f"  Reported baseline (cert-abridge, Tranco): p5/p50/p95 = {CERT_ABRIDGE_P5_P50_P95}")
    print(f"\nserved depth: {stats['depth']}")
    print(f"ICA count: " + ", ".join(f"{k}: {v['n']} ({v['pct']}%)" for k, v in stats["ica"].items()))
    print(f"  Reported baseline (Sikeridis 2022): {SIKERIDIS_ICA}")
    print(f"root transmitted: {root_tx} ({stats['root_transmitted']['pct']}%)")
    print(f"\nleaf key alg: " + ", ".join(f"{k}: {v['n']} ({v['pct']}%)" for k, v in stats["leaf_key_alg"].items()))
    print(f"  Reported baseline (arXiv:2607.29005): {LONGITUDINAL_LEAF}")
    print(f"leaf SCT count: {stats['leaf_sct_count']}")
    print(f"leaf SANs: p50={stats['leaf_san']['p50']} p95={stats['leaf_san']['p95']} max={stats['leaf_san']['max']}")
    print("\nsize spread at fixed depth (the variance signal):")
    for d, s in spread.items():
        print(f"  depth {d}: n={s['n']} p5={s['p5']} p50={s['p50']} p95={s['p95']} p95/p5={s['p95_over_p5']}x")
    print(f"\nfailures: {stats['failures']}")
    print(f"cert parse errors: {parse_errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
