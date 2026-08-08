#!/usr/bin/env python3
"""Project each captured chain to its post-quantum equivalent (Phase 2/3).

Every output figure is PROPOSED: a projection under the stated assumptions,
computed from each site's own measured certificate content. Inputs are the
summary JSONL from parse_chains.py (which records the measured signature and
SPKI byte sizes per certificate; those are the only fields the projection
swaps).

Scenario axes (all combinations emitted, never one number):
  param:     ML-DSA-44 | ML-DSA-65
  scts:      classical (SCTs keep ECDSA logs) | migrated (each SCT signature
             becomes an ML-DSA signature)
  migration: full (every transmitted cert re-signed and re-keyed) |
             leaf-only (leaf gets an ML-DSA key, chain signatures stay
             classical; CertificateVerify still becomes ML-DSA)

Assumptions, stated once and carried by every consumer:
  - DER length-prefix growth from long-form lengths is ignored (a few bytes).
  - Chain depth, SAN/extension content, and root transmission stay exactly as
    observed. Sites that transmit their root pay its migration bytes too.
  - Each embedded SCT today carries a ~71-byte ECDSA signature (typical P-256).
  - Certificate message framing: 12 bytes plus 5 per certificate.
  - Non-CertificateVerify flight overhead is 1,256 bytes: derived from
    pqc-cert-matrix phase3/TRANSPORT.md, where measured flight minus
    Certificate minus CertificateVerify is 1,256 for all four chain families.
    Lab value for one stack; real servers vary with ALPN and extensions.
  - CertificateVerify is signature size plus 4 bytes framing (same source).
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import product
from pathlib import Path
from typing import Any

# Verified locally 2026-08-07 against OpenSSL 3.5.5 (scripts/measure-mldsa-sizes.sh).
# Raw sizes match FIPS 204; spki includes the DER SubjectPublicKeyInfo wrapper.
MLDSA = {
    "ML-DSA-44": {"spki": 1334, "sig": 2420},
    "ML-DSA-65": {"spki": 1974, "sig": 3309},
    "ML-DSA-87": {"spki": 2614, "sig": 4627},
}
SCT_CLASSICAL_SIG = 71  # typical ECDSA P-256 SCT signature, assumption
NON_CV_OVERHEAD = 1256  # Reported: pqc-cert-matrix phase3/TRANSPORT.md, see module docstring
CV_FRAMING = 4
WINDOWS = {"IW10": 14600, "IW20": 29200, "IW32": 46720}
AMP_3X = 4071  # 3 x 1,357: the larger QUIC amplification limit Nawrocki et al. use

PARAMS = ("ML-DSA-44", "ML-DSA-65")
SCT_MODES = ("classical", "migrated")
MIGRATIONS = ("full", "leaf-only")


def project_domain(rec: dict[str, Any], param: str, scts: str, migration: str) -> dict[str, Any] | None:
    certs = rec.get("certs") or []
    if not certs or any("parse_error" in c for c in certs):
        return None
    sizes = MLDSA[param]
    projected: list[int] = []
    for i, c in enumerate(certs):
        der = c["der_len"]
        if migration == "full":
            der = der - c["sig_len"] - c["spki_len"] + sizes["sig"] + sizes["spki"]
        elif i == 0:  # leaf-only: new key in the leaf, classical signature kept
            der = der - c["spki_len"] + sizes["spki"]
        if i == 0 and scts == "migrated":
            der += c.get("sct_count", 0) * (sizes["sig"] - SCT_CLASSICAL_SIG)
        projected.append(der)

    chain_wire = sum(projected) + 12 + 5 * len(projected)
    cert_verify = sizes["sig"] + CV_FRAMING
    flight = chain_wire + cert_verify + NON_CV_OVERHEAD
    return {
        "domain": rec["domain"],
        "rank": rec.get("rank"),
        "scenario": {"param": param, "scts": scts, "migration": migration},
        "classical_chain_der": rec["total_der_bytes"],
        "projected_chain_der": sum(projected),
        "projected_flight": flight,
        "fits": {w: flight <= limit for w, limit in WINDOWS.items()},
        "chain_over_amp_3x": sum(projected) > AMP_3X,
    }


def pctile(vals: list[int], p: float) -> int:
    return vals[min(len(vals) - 1, int(p / 100 * len(vals)))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="summary JSONL from parse_chains.py")
    ap.add_argument("--output", type=Path, help="optional per-domain projection JSONL")
    args = ap.parse_args()

    recs = [json.loads(l) for l in args.input.open() if '"_meta"' not in l[:12]]
    ok = [r for r in recs if r.get("ok")]
    out = args.output.open("w") if args.output else None

    print(f"projecting {len(ok)} domains (PROPOSED figures; assumptions in module docstring)\n")
    header = f"{'scenario':44} {'p50 flight':>10} {'p95 flight':>10} {'>IW10':>7} {'>IW20':>7} {'>amp3x':>7}"
    print(header)
    skipped = 0
    for param, scts, migration in product(PARAMS, SCT_MODES, MIGRATIONS):
        rows = []
        for r in ok:
            p = project_domain(r, param, scts, migration)
            if p is None:
                skipped += 1
                continue
            rows.append(p)
            if out:
                out.write(json.dumps(p) + "\n")
        flights = sorted(x["projected_flight"] for x in rows)
        over_iw10 = sum(1 for x in rows if not x["fits"]["IW10"]) / len(rows) * 100
        over_iw20 = sum(1 for x in rows if not x["fits"]["IW20"]) / len(rows) * 100
        over_amp = sum(1 for x in rows if x["chain_over_amp_3x"]) / len(rows) * 100
        label = f"{param} scts={scts} migration={migration}"
        print(f"{label:44} {pctile(flights, 50):>10,} {pctile(flights, 95):>10,} {over_iw10:>6.1f}% {over_iw20:>6.1f}% {over_amp:>6.1f}%")
    if out:
        out.close()
    print(f"\nskipped domain-scenarios (unparseable certs): {skipped}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
