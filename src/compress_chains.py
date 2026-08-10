#!/usr/bin/env python3
"""Certificate compression (RFC 8879) on the captured corpus, and after migration.

Three questions, in order:

1. What does certificate compression actually save on the chains real sites
   serve? Verified against the captured evidence.
2. How does that saving decompose into redundancy inside each certificate
   against redundancy across certificates in the chain? Verified.
3. Held against a chain migrated to ML-DSA, what does the same saving become?
   Proposed, and the assumption that makes it work is stated below.

The projection holds the measured structural saving constant and grows the
payload by the FIPS 204 delta per certificate, the same swap project_chains.py
performs. That is sound only because ML-DSA signatures and public keys carry no
compressible redundancy: measured in pqc-cert-matrix, an ML-DSA signature comes
out of zlib, brotli, and zstd four bytes LARGER than it went in, at every
parameter set (Reported, see MLDSA_INCOMPRESSIBLE below). No compression was run
against a migrated chain, because the corpus contains no post-quantum
certificates to run it against.

Payload is the concatenated DER certificate_list in wire order, exactly as
captured. Stated approximation, same as pqc-cert-matrix phase3: this is the
certificate_list, not the byte-exact Certificate handshake message, which adds
roughly 15 bytes of framing (handshake header, list length, and a per-
certificate length and extensions field).

Every algorithm runs at its library maximum (zlib 9, brotli 11, zstd 22), so
these are an upper bound on the saving. A production server picks something
cheaper and saves less.

Requires the `brotli` and `zstandard` packages in addition to the repo's usual
dependencies.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
import zlib
from collections import Counter
from pathlib import Path
from typing import Any

import brotli
import zstandard

# Verified locally 2026-08-07 against OpenSSL 3.5.5 (scripts/measure-mldsa-sizes.sh).
# Copied from project_chains.py so the two projections cannot drift apart.
MLDSA = {
    "ML-DSA-44": {"spki": 1334, "sig": 2420},
    "ML-DSA-65": {"spki": 1974, "sig": 3309},
}

# Reported: draft-ietf-tls-cert-abridge-02 Table 1, ~75,000 Tranco chains. The
# caption states the row used "ZStandard with the parameters configured for
# maximum compression", so the comparison below is against our zstd column, not
# our best-of-three. This is the measurement our corpus work refines; it is NOT
# preempted by us and must be cited wherever our percentiles appear.
CERT_ABRIDGE_ORIGINAL = (2308, 4032, 5609)  # p5 / p50 / p95
CERT_ABRIDGE_ZSTD = (1619, 3243, 3821)

# Reported: pqc-cert-matrix phase3, measured against real ML-DSA certificates.
# Compressing an ML-DSA signature or SPKI grows it by exactly 4 bytes of
# compressor framing at every parameter set and every RFC 8879 algorithm.
MLDSA_INCOMPRESSIBLE = 4


def compress_all(payload: bytes, zc: zstandard.ZstdCompressor) -> dict[str, int]:
    """Maximum-effort compressed length under each RFC 8879 algorithm."""
    return {
        "zlib": len(zlib.compress(payload, 9)),
        "brotli": len(brotli.compress(payload, quality=11)),
        "zstd": len(zc.compress(payload)),
    }


def measure(certs: list[bytes], zc: zstandard.ZstdCompressor) -> dict[str, Any]:
    """Compression of one chain, decomposed.

    `within` is what compression finds inside individual certificates (X.509
    boilerplate, OIDs, repeated extension structure). `across` is the remainder
    of the joint saving, which is what compression finds only when the
    certificates are sent together, chiefly the issuer name in each certificate
    repeating the subject name of the next one up.
    """
    payload = b"".join(certs)
    joint = compress_all(payload, zc)
    algo = min(joint, key=joint.get)
    saving = len(payload) - joint[algo]
    within = sum(len(c) - min(compress_all(c, zc).values()) for c in certs)
    return {
        "certs": len(certs),
        "raw": len(payload),
        "compressed": joint[algo],
        "algo": algo,
        "zstd": joint["zstd"],
        "saving": saving,
        "within": within,
        "across": saving - within,
    }


def pctile(vals: list[float], p: float) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(p / 100 * len(s)))]


def fmt(vals: list[float], unit: str = "", dp: int = 0) -> str:
    return (f"p5 {pctile(vals, 5):,.{dp}f}{unit} / p50 {pctile(vals, 50):,.{dp}f}{unit} "
            f"/ p95 {pctile(vals, 95):,.{dp}f}{unit}")


def load_capture(path: Path) -> dict[str, list[bytes]]:
    opener = gzip.open if path.suffix == ".gz" else open
    out: dict[str, list[bytes]] = {}
    with opener(path, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("ok") and r.get("certs_der_b64"):
                out[r["domain"]] = [base64.b64decode(c) for c in r["certs_der_b64"]]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--capture", required=True, type=Path,
                    help="raw capture JSONL(.gz) from capture_chains.py")
    ap.add_argument("--summary", required=True, type=Path,
                    help="parsed summary JSONL from parse_chains.py (for the projection)")
    ap.add_argument("--output", type=Path, help="optional per-chain JSON")
    args = ap.parse_args()

    zc = zstandard.ZstdCompressor(level=22)
    chains = load_capture(args.capture)
    print(f"compressing {len(chains):,} captured chains at maximum effort", file=sys.stderr)
    rows = {d: measure(c, zc) | {"domain": d} for d, c in chains.items()}
    vals = list(rows.values())

    print("\n== Verified: compression on the chains real sites serve ==")
    print(f"chains          : {len(vals):,}")
    print(f"raw payload     : {fmt([r['raw'] for r in vals], ' B')}")
    print(f"zstd compressed : {fmt([r['zstd'] for r in vals], ' B')}")
    print(f"  Reported, draft-ietf-tls-cert-abridge-02 over ~75,000 Tranco chains:")
    print(f"    original {CERT_ABRIDGE_ORIGINAL}, zstd {CERT_ABRIDGE_ZSTD}")
    print(f"saving (best)   : {fmt([r['saving'] for r in vals], ' B')}")
    print(f"saving (best) % : {fmt([r['saving'] / r['raw'] * 100 for r in vals], '%', 1)}")
    print(f"saving (zstd)   : {fmt([r['raw'] - r['zstd'] for r in vals], ' B')}")

    print("\nwinning algorithm:")
    for a, c in Counter(r["algo"] for r in vals).most_common():
        print(f"  {a:7s} {c:6,} ({c / len(vals) * 100:5.1f}%)")
    print(f"  brotli's median advantage over zstd: "
          f"{pctile([r['zstd'] - r['compressed'] for r in vals], 50):,.0f} B")

    print("\ndecomposition of the saving (median):")
    print(f"  inside certificates : {pctile([r['within'] for r in vals], 50):,.0f} B")
    print(f"  across certificates : {pctile([r['across'] for r in vals], 50):,.0f} B")

    print("\nby chain depth:")
    by: dict[int, list[dict[str, Any]]] = {}
    for r in vals:
        by.setdefault(r["certs"], []).append(r)
    for k in sorted(by):
        g = by[k]
        if len(g) < 20:
            continue
        print(f"  {k} certs  n={len(g):5,}  raw p50 {pctile([x['raw'] for x in g], 50):6,.0f} B"
              f"  saving p50 {pctile([x['saving'] for x in g], 50):5,.0f} B"
              f"  ({pctile([x['saving'] / x['raw'] * 100 for x in g], 50):4.1f}%)")

    print("\n== Proposed: the same saving against a migrated chain ==")
    print(f"(structural saving held constant; ML-DSA fields compress to "
          f"+{MLDSA_INCOMPRESSIBLE} bytes, Reported from pqc-cert-matrix)")
    proj: dict[str, list[dict[str, float]]] = {p: [] for p in MLDSA}
    skipped = 0
    for line in args.summary.open():
        r = json.loads(line)
        if not r.get("ok") or r["domain"] not in rows:
            continue
        # A certificate whose signature or SPKI did not parse cannot be
        # projected; drop the whole chain rather than project part of it.
        if any("sig_len" not in c or "spki_len" not in c for c in r["certs"]):
            skipped += 1
            continue
        m = rows[r["domain"]]
        for param, sizes in MLDSA.items():
            delta = sum((sizes["sig"] - c["sig_len"]) + (sizes["spki"] - c["spki_len"])
                        for c in r["certs"])
            proj[param].append({"raw": m["raw"] + delta, "saving": m["saving"],
                                "pct": m["saving"] / (m["raw"] + delta) * 100})

    n_proj = len(next(iter(proj.values())))
    print(f"chains projected: {n_proj:,} (dropped {skipped} for unparsed fields)")
    now = [r["saving"] / r["raw"] * 100 for r in vals]
    print(f"  classical today : payload p50 {pctile([r['raw'] for r in vals], 50):,.0f} B, "
          f"saving p50 {pctile([r['saving'] for r in vals], 50):,.0f} B "
          f"({pctile(now, 50):.1f}%)")
    for param, g in proj.items():
        print(f"  {param}      : payload p50 {pctile([r['raw'] for r in g], 50):,.0f} B, "
              f"saving p50 {pctile([r['saving'] for r in g], 50):,.0f} B "
              f"({pctile([r['pct'] for r in g], 50):.1f}%)  "
              f"[{fmt([r['pct'] for r in g], '%', 1)}]")

    if args.output:
        args.output.write_text(json.dumps(vals))
        print(f"\nwrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
