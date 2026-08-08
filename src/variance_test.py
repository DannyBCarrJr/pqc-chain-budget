#!/usr/bin/env python3
"""Phase 4: does measured per-site content beat the constant-delta model?

The hostile-reviewer position (PRIOR-ART.md): a PQ projection is just the
classical distribution shifted by (depth x a constant), so measuring each
site's certificate content adds nothing. This script tests that claim three
ways, most favorable to the reviewer first:

  B1-EC / B1-RSA: the reviewer gets our measured classical chain totals and
    per-site depth, and applies a constant per-certificate delta assuming a
    typical ECDSA (sig 72, SPKI 91) or RSA-2048 (sig 256, SPKI 294) chain.
    Deviation from the measured-content projection then comes ONLY from
    per-cert signature/SPKI sizes differing from the assumed constant, which
    is exactly the content-measurement contribution, isolated.
  A (literature-only): no corpus access at all. cert-abridge's published p50
    classical chain plus Sikeridis 2022's depth mix plus the delta arithmetic.

Metric that matters: IW verdict flips. "false pass" = model says fits,
measured says blows (dangerous); "false alarm" = the reverse. All figures
Proposed, same assumptions as project_chains.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from project_chains import CV_FRAMING, MLDSA, NON_CV_OVERHEAD, WINDOWS, pctile, project_domain

CONST = {"EC": {"sig": 72, "spki": 91}, "RSA": {"sig": 256, "spki": 294}}
# Sikeridis ePrint 2022/1556 Table 2 midpoints (0/1/2/3 ICAs), normalized.
SIKERIDIS_DEPTH_MIX = {1: 0.22, 2: 0.40, 3: 0.27, 4: 0.105}
CERT_ABRIDGE_P50 = 4032


def const_model_flight(rec: dict[str, Any], param: str, flavor: str) -> int:
    certs = rec["certs"]
    c = CONST[flavor]
    s = MLDSA[param]
    delta_per_cert = (s["sig"] + s["spki"]) - (c["sig"] + c["spki"])
    chain = rec["total_der_bytes"] + len(certs) * delta_per_cert
    return chain + 12 + 5 * len(certs) + s["sig"] + CV_FRAMING + NON_CV_OVERHEAD


def literature_only_p50(param: str, flavor: str) -> float:
    s = MLDSA[param]
    c = CONST[flavor]
    e_depth = sum(d * w for d, w in SIKERIDIS_DEPTH_MIX.items()) / sum(SIKERIDIS_DEPTH_MIX.values())
    delta = (s["sig"] + s["spki"]) - (c["sig"] + c["spki"])
    chain = CERT_ABRIDGE_P50 + e_depth * delta
    return chain + 12 + 5 * e_depth + s["sig"] + CV_FRAMING + NON_CV_OVERHEAD


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="summary JSONL from parse_chains.py")
    args = ap.parse_args()

    recs = [json.loads(l) for l in args.input.open() if '"_meta"' not in l[:12]]
    ok = [r for r in recs if r.get("ok") and r.get("certs") and not any("parse_error" in c for c in r["certs"])]

    for param in ("ML-DSA-44", "ML-DSA-65"):
        print(f"\n=== {param}, full-chain migration, classical SCTs ===")
        measured = []
        for r in ok:
            p = project_domain(r, param, "classical", "full")
            if p:
                measured.append((r, p["projected_flight"]))
        mf = sorted(f for _, f in measured)
        print(f"measured-content: p50={pctile(mf, 50):,} p95={pctile(mf, 95):,}")

        for flavor in ("EC", "RSA"):
            model = [(r, const_model_flight(r, param, flavor)) for r, _ in measured]
            bf = sorted(f for _, f in model)
            devs = sorted(m - b for (_, m), (_, b) in zip(measured, model))
            n = len(measured)
            for w, limit in (("IW10", WINDOWS["IW10"]), ("IW20", WINDOWS["IW20"])):
                false_pass = sum(1 for (_, m), (_, b) in zip(measured, model) if b <= limit < m)
                false_alarm = sum(1 for (_, m), (_, b) in zip(measured, model) if m <= limit < b)
                print(
                    f"  B1-{flavor:3} vs {w}: false-pass {false_pass} ({false_pass/n*100:.1f}%), "
                    f"false-alarm {false_alarm} ({false_alarm/n*100:.1f}%)"
                )
            print(
                f"  B1-{flavor:3} model p50={pctile(bf, 50):,} p95={pctile(bf, 95):,}; "
                f"deviation (measured - model) p5={devs[int(.05*n)]:,} p50={devs[n//2]:,} p95={devs[int(.95*n)]:,}"
            )
            print(f"  A (literature-only, {flavor}-typical) p50={literature_only_p50(param, flavor):,.0f}")

    # SCT-count assumption test: migrated-SCT scenario, constant s vs measured s.
    print("\n=== SCT migration scenario: constant SCT-count assumption vs measured (ML-DSA-44, full) ===")
    rows = []
    for r in ok:
        p = project_domain(r, "ML-DSA-44", "migrated", "full")
        if p:
            rows.append((r, p["projected_flight"]))
    n = len(rows)
    sig = MLDSA["ML-DSA-44"]["sig"]
    for s_const in (2, 3):
        flips = 0
        for r, m in rows:
            actual_s = r["certs"][0].get("sct_count", 0)
            model_flight = m + (s_const - actual_s) * (sig - 71)
            if (model_flight <= WINDOWS["IW20"]) != (m <= WINDOWS["IW20"]):
                flips += 1
        print(f"  assume every site has {s_const} SCTs: {flips} IW20 verdict flips ({flips/n*100:.1f}%)")

    print(f"\ndomains tested: {len(ok)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
