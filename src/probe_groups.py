#!/usr/bin/env python3
"""Deferred-field subsample: negotiated TLS group and certificate compression.

Python's ssl module (3.14) exposes neither field, so this pass drives
`openssl s_client` (3.5.5, whose default ClientHello offers X25519MLKEM768;
verified against cloudflare.com and google.com 2026-08-07) over a rank-strided
subsample of domains that already completed capture. One extra connection per
sampled domain.

The negotiated group is client-relative: it reports what the server picks when
offered this client's defaults, comparable to the published adoption scans.

CompressedCertificate detection reads the -trace output for the handshake
message name. Verified 2026-08-10 against six live hosts: the pattern matches
only the received `CompressedCertificate` message and never the client's own
`compress_certificate(27)` offer, which every ClientHello carries (the extension
name has no "ed", so `compressed.?` cannot reach its "certificate"). The three
hits this finds are real zstd messages and they reproduce.

Compression detection is also client-relative, and more narrowly than the group
is: this build advertises `zlib (1)` and `zstd (3)` only, so a brotli-only server
reads as a non-engagement. pqc-cert-matrix once recorded a uniform lab zero as a
client-side finding; that reading was wrong and was retracted 2026-08-10. The
client negotiates compression fine when the server offers it.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

GROUP_RE = re.compile(r"Negotiated TLS1\.3 group: (\S+)")
PROTO_RE = re.compile(r"^Protocol\s*: (\S+)", re.M)
NAMED_RE = re.compile(r"NamedGroup: (.+?) \(\d+\)")
# Anchored to the start of a trace line so this can only ever match the
# handshake message name, never prose or an extension name elsewhere in the
# output. Format verified against live traces 2026-08-10:
#     CompressedCertificate, Length=2227
#       Compression type=zstd (0x0003)
COMPCERT_RE = re.compile(r"^\s*CompressedCertificate\b", re.M)
COMPALG_RE = re.compile(r"^\s*Compression type=(\S+)", re.M)


def probe(rec: dict[str, Any], timeout: float) -> dict[str, Any]:
    host = rec.get("hostname") or rec["domain"]
    out: dict[str, Any] = {"domain": rec["domain"], "rank": rec.get("rank"), "hostname": host}
    try:
        proc = subprocess.run(
            ["openssl", "s_client", "-connect", f"{host}:443", "-servername", host, "-trace"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        text = proc.stdout + proc.stderr
        group = GROUP_RE.search(text)
        named = NAMED_RE.findall(text)
        proto = PROTO_RE.search(text)
        out.update(
            ok=bool(proto),
            # Two independent reads of the negotiated group from one
            # connection: the summary line (prints for KEM exchanges) and the
            # last key_share NamedGroup in the trace (the ServerHello's
            # choice, validated against an office.com HRR transcript).
            # Disagreement between them is recorded, never papered over.
            # Trace fallback is valid ONLY for TLS 1.3: a TLS 1.2 server
            # sends no key_share, so the last NamedGroup in its trace is the
            # client's own offer (this mislabeled 177 TLS 1.2 sessions as
            # hybrid before the guard; caught by cross-tab 2026-08-07).
            group=group.group(1) if group else (
                named[-1].split()[0] if named and proto and proto.group(1) == "TLSv1.3" else None),
            group_line=group.group(1) if group else None,
            group_trace=named[-1].split()[0] if named else None,
            protocol=proto.group(1) if proto else None,
            # HRR fingerprint: a received key_share carrying only the 2-byte
            # selected_group ("HelloRetryRequest" never appears literally).
            hello_retry="extension_type=key_share(51), length=2" in text,
            compressed_cert=bool(COMPCERT_RE.search(text)),
            # Ships the algorithm alongside the boolean so the claim carries its
            # own evidence instead of resting on a re-probe.
            compression_alg=(m.group(1) if (m := COMPALG_RE.search(text)) else None),
        )
    except subprocess.TimeoutExpired:
        out.update(ok=False, group=None, protocol=None, compressed_cert=False, error="timeout")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="summary JSONL from parse_chains.py")
    ap.add_argument("--output", required=True, type=Path, help="probe results JSONL")
    ap.add_argument("--stride", type=int, default=8, help="sample every Nth successful domain by rank")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args()

    recs = [json.loads(l) for l in args.input.open() if '"_meta"' not in l[:12]]
    ok = sorted((r for r in recs if r.get("ok")), key=lambda r: r.get("rank") or 0)
    sample = ok[:: args.stride]
    print(f"probing {len(sample)} of {len(ok)} successful domains (stride {args.stride})", file=sys.stderr)

    results: list[dict[str, Any]] = []
    with args.output.open("w") as out:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for res in pool.map(lambda r: probe(r, args.timeout), sample):
                results.append(res)
                out.write(json.dumps(res) + "\n")

    live = [r for r in results if r.get("ok")]
    groups = Counter(r["group"] or "none/TLS1.2" for r in live)
    protos = Counter(r["protocol"] for r in live)
    hybrid = sum(v for k, v in groups.items() if "MLKEM" in k)
    compressed = sum(1 for r in live if r["compressed_cert"])
    print(f"\nprobed ok: {len(live)}/{len(results)}")
    print("negotiated group:", {k: f"{v} ({v/len(live)*100:.1f}%)" for k, v in groups.most_common(8)})
    print(f"hybrid PQ key exchange: {hybrid}/{len(live)} ({hybrid/len(live)*100:.1f}%)")
    print("protocol:", dict(protos.most_common()))
    # RFC 8879 is TLS 1.3 only, so a TLS 1.2 session could never have compressed.
    # Report against the denominator that could actually have engaged.
    tls13 = sum(1 for r in live if r.get("protocol") == "TLSv1.3")
    algs = Counter(r["compression_alg"] for r in live if r.get("compression_alg"))
    print(f"CompressedCertificate seen: {compressed}/{tls13} TLS1.3 sessions "
          f"({compressed/tls13*100:.2f}%) {dict(algs) or ''}")
    hrr = sum(1 for r in live if r.get("hello_retry"))
    print(f"HelloRetryRequest (server refused the offered key share): {hrr} ({hrr/len(live)*100:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
