#!/usr/bin/env python3
"""Capture served TLS certificate chains for a list of domains.

Evidence-only capture: one JSON line per domain holding the chain exactly as
served (base64 DER) plus handshake basics. All derivation happens in
parse_chains.py, so the corpus is scanned once and re-analyzed forever.

Politeness: one handshake per domain, a single www. fallback when the apex
fails, one retry on transient errors only. No HTTP request is ever sent; this
is the same act a browser performs before its first byte of HTTP.

Supports resume: domains already present in the output file are skipped.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import socket
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path

TRANSIENT = (TimeoutError, ConnectionResetError, BrokenPipeError, ssl.SSLEOFError)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def handshake(hostname: str, timeout: float, connect_addr: str | None = None) -> dict[str, object]:
    ctx = ssl.create_default_context()
    # Verification is disabled ON PURPOSE. This is a measurement instrument,
    # not a client: the point is to record the chain exactly as served,
    # including invalid, expired and self-signed ones, which verification
    # would silently exclude and bias the corpus. No application data is ever
    # sent on the connection, so there is nothing for a MITM to steal;
    # validity is an analysis question, answered offline in parse_chains.py.
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    # connect_addr lets a caller connect to an address it has already resolved
    # and vetted (the live checker pins the vetted IP so a second lookup cannot
    # be rebound to a private address); SNI still carries the hostname either
    # way. Corpus capture passes nothing and behaves exactly as before.
    with socket.create_connection((connect_addr or hostname, 443), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as tls:
            chain = tls.get_unverified_chain() or []
            cipher = tls.cipher()
            return {
                "tls_version": tls.version(),
                "cipher": cipher[0] if cipher else None,
                "certs_der_b64": [base64.b64encode(der).decode("ascii") for der in chain],
            }


def capture(rank: int | None, domain: str, timeout: float) -> dict[str, object]:
    base: dict[str, object] = {"rank": rank, "domain": domain, "ts": utcnow()}
    hostnames = [domain] if domain.startswith("www.") else [domain, "www." + domain]
    last_host, last_err = domain, "unattempted"
    for hostname in hostnames:
        err = None
        for attempt in (1, 2):  # first try plus one retry, transient errors only
            try:
                data = handshake(hostname, timeout)
                return {**base, "ok": True, "hostname": hostname, "error": None, **data}
            except TRANSIENT as e:
                err = f"{type(e).__name__}: {e}"
            except (ssl.SSLError, OSError) as e:  # definitive: no retry, try fallback host
                err = f"{type(e).__name__}: {e}"
                break
        last_host, last_err = hostname, err or "unknown"
    return {**base, "ok": False, "hostname": last_host, "error": last_err}


def read_corpus(path: Path) -> list[tuple[int | None, str]]:
    rows: list[tuple[int | None, str]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if "," in line:
            rank_s, domain = line.split(",", 1)
            rows.append((int(rank_s), domain.strip()))
        else:
            rows.append((None, line))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="CSV rank,domain or plain domain lines")
    ap.add_argument("--output", required=True, type=Path, help="raw capture JSONL (appended; resume-safe)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N domains (0 = all)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--timeout", type=float, default=8.0)
    args = ap.parse_args()

    rows = read_corpus(args.input)
    if args.limit:
        rows = rows[: args.limit]

    done: set[str] = set()
    if args.output.exists():
        for line in args.output.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "domain" in rec:
                done.add(rec["domain"])
    todo = [(r, d) for r, d in rows if d not in done]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a") as out:
        meta = {
            "_meta": {
                "started": utcnow(),
                "python": sys.version.split()[0],
                "openssl": ssl.OPENSSL_VERSION,
                "input": str(args.input),
                "workers": args.workers,
                "timeout": args.timeout,
                "todo": len(todo),
                "skipped_done": len(done),
            }
        }
        out.write(json.dumps(meta) + "\n")
        out.flush()
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(capture, rank, domain, args.timeout) for rank, domain in todo]
            for fut in concurrent.futures.as_completed(futures):
                out.write(json.dumps(fut.result()) + "\n")
                completed += 1
                if completed % 250 == 0:
                    out.flush()
                    print(f"{completed}/{len(todo)}", file=sys.stderr)
        out.flush()
    print(f"done: {completed} captured, {len(done)} previously present", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
