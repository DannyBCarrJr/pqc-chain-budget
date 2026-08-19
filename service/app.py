#!/usr/bin/env python3
"""Live chain check API: measure one domain's served chain on demand.

The corpus tool at carrdigital.dev/tools/chain-check/ answers from a static
snapshot of the Tranco top 10k. This service answers for every other domain:
one GET, one handshake, the same capture -> parse -> project pipeline the
corpus went through, returned in the exact row shape the page already renders.
The measurement code is imported from src/, not copied, so the live path
cannot drift from the published method.

Guardrails, because "measure any host" is an SSRF primitive if left bare:
  - hostnames only, port fixed at 443, IDNA-normalized before anything else
  - every resolved address is vetted and only globally routable IPs are
    dialed; the connection pins the vetted address so a second resolution
    cannot rebind to something private
  - a per-client hourly budget, a global concurrency cap, and a result cache
    (success 24h, failure 10 min) keep one page's traffic from becoming a scan
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
import re
import socket
import ssl
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from capture_chains import TRANSIENT, handshake, utcnow
from export_web import SCENARIOS
from parse_chains import summarize
from project_chains import project_domain

ALLOW_ORIGINS = os.environ.get("ALLOW_ORIGINS", "https://carrdigital.dev").split(",")
BUDGET_PER_HOUR = int(os.environ.get("BUDGET_PER_HOUR", "20"))
CACHE_OK_TTL = int(os.environ.get("CACHE_OK_TTL", str(24 * 3600)))
CACHE_ERR_TTL = int(os.environ.get("CACHE_ERR_TTL", "600"))
CACHE_MAX = int(os.environ.get("CACHE_MAX", "50000"))
HANDSHAKE_TIMEOUT = float(os.environ.get("HANDSHAKE_TIMEOUT", "8.0"))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "4"))

LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


def normalize(raw: str) -> str | None:
    """Mirror the page's normalize(), then be stricter: the page only builds a
    lookup key, this side opens sockets. Returns an IDNA ASCII hostname or
    None for anything that is not a plain public hostname."""
    d = raw.strip().lower()
    d = re.sub(r"^[a-z][a-z0-9+.-]*://", "", d)
    d = re.sub(r"[/?#].*$", "", d)
    d = re.sub(r":\d+$", "", d)
    d = d.rstrip(".")
    d = d.removeprefix("www.")
    if not d or len(d) > 253:
        return None
    try:
        d = d.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    labels = d.split(".")
    if len(labels) < 2 or not all(LABEL.match(label) for label in labels):
        return None
    # An all-digit final label is an IPv4 literal, and IPv6 never survives
    # LABEL. Names only: an address has no SNI story and no corpus analog.
    if not any(c.isalpha() for c in labels[-1]):
        return None
    return d


def resolve_global(hostname: str) -> tuple[list[str], bool]:
    """(globally routable addresses, whether the name resolved at all)."""
    try:
        infos = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return [], False
    addrs: list[str] = []
    for *_, sockaddr in infos:
        addr = sockaddr[0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if ip.is_global and not ip.is_multicast and addr not in addrs:
            addrs.append(addr)
    return addrs, True


def measure(domain: str) -> dict:
    """One live capture with corpus semantics: apex then www fallback, one
    retry on transient errors only, connections pinned to vetted addresses."""
    base: dict[str, object] = {"domain": domain, "ts": utcnow()}
    hostnames = [domain, "www." + domain]
    last_err, code = "unattempted", "dns"
    for hostname in hostnames:
        addrs, resolved = resolve_global(hostname)
        if not resolved:
            last_err, code = f"{hostname} does not resolve", "dns"
            continue
        if not addrs:
            last_err, code = f"{hostname} resolves only to non-public addresses", "private"
            continue
        for addr in addrs[:2]:
            err = None
            for _ in (1, 2):
                try:
                    data = handshake(hostname, HANDSHAKE_TIMEOUT, connect_addr=addr)
                    return {**base, "ok": True, "hostname": hostname, "error": None, **data}
                except TRANSIENT as e:
                    err = f"{type(e).__name__}: {e}"
                except (ssl.SSLError, OSError) as e:
                    err = f"{type(e).__name__}: {e}"
                    break
            last_err, code = err or "unknown", "handshake"
    return {**base, "ok": False, "error": last_err, "error_code": code}


def build_payload(raw: dict) -> dict | None:
    """Parse and project a live capture into the corpus shard row shape
    (export_web.py row_fields), so the page renders both identically."""
    rec = summarize(raw)
    if not rec.get("ok") or not rec.get("certs"):
        return None
    flights: list[int] = []
    for p, s, m in SCENARIOS:
        proj = project_domain(rec, p, s, m)
        if proj is None:
            return None
        flights.append(proj["projected_flight"])
    leaf = rec["certs"][0]
    return {
        "domain": rec["domain"],
        "hostname": rec["hostname"],
        "ts": rec["ts"],
        "tls_version": rec.get("tls_version"),
        "row": [
            None,
            rec["total_der_bytes"],
            rec["depth"],
            leaf.get("sct_count", 0),
            1 if rec["root_transmitted"] else 0,
            leaf.get("pubkey_alg", "?").split("-")[0],
            flights,
        ],
    }


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    CORSMiddleware, allow_origins=ALLOW_ORIGINS, allow_methods=["GET"], allow_headers=[]
)

# domain -> (monotonic expiry, payload, http status)
_cache: dict[str, tuple[float, dict, int]] = {}
_hits: dict[str, deque[float]] = defaultdict(deque)
_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
_sem = asyncio.Semaphore(MAX_CONCURRENT)


def client_ip(request: Request) -> str:
    # ponytail: header-derived identity is best-effort abuse damping, not a
    # security boundary; a spoofed header only reshuffles budgets. The hard
    # ceilings are the global semaphore and the cache. Upgrade path: rate
    # limit at the edge (Cloudflare) in front of this and trust only its header.
    fwd = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "")
    first = fwd.split(",")[0].strip()
    return first or (request.client.host if request.client else "?")


def over_budget(ip: str) -> bool:
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= BUDGET_PER_HOUR:
        return True
    q.append(now)
    return False


def cache_put(domain: str, payload: dict, status: int) -> None:
    if len(_cache) >= CACHE_MAX:
        now = time.monotonic()
        for k in [k for k, v in _cache.items() if v[0] <= now]:
            del _cache[k]
        # ponytail: if 50k live entries are all still fresh, drop the oldest
        # insertions rather than refusing; dict order is insertion order.
        while len(_cache) >= CACHE_MAX:
            del _cache[next(iter(_cache))]
        _locks.clear()
        for k in [k for k, v in _hits.items() if not v]:
            del _hits[k]
    ttl = CACHE_OK_TTL if status == 200 else CACHE_ERR_TTL
    _cache[domain] = (time.monotonic() + ttl, payload, status)


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True, "python": sys.version.split()[0], "openssl": ssl.OPENSSL_VERSION}


@app.get("/check")
async def check(request: Request, domain: str = "") -> JSONResponse:
    d = normalize(domain)
    if d is None:
        return JSONResponse(
            {"error": "invalid", "detail": "not a hostname this tool measures"}, status_code=400
        )
    hit = _cache.get(d)
    if hit and hit[0] > time.monotonic():
        return JSONResponse(hit[1], status_code=hit[2], headers={"x-cache": "hit"})
    if over_budget(client_ip(request)):
        return JSONResponse(
            {
                "error": "budget",
                "detail": f"over {BUDGET_PER_HOUR} live measurements this hour; try again later",
            },
            status_code=429,
        )
    async with _locks[d]:
        hit = _cache.get(d)  # someone else may have settled it while we waited
        if hit and hit[0] > time.monotonic():
            return JSONResponse(hit[1], status_code=hit[2], headers={"x-cache": "hit"})
        async with _sem:
            raw = await asyncio.to_thread(measure, d)
        if raw["ok"]:
            payload = build_payload(raw)
            if payload is None:
                payload, status = (
                    {"error": "parse", "detail": f"{d} served a chain this tool could not parse"},
                    502,
                )
            else:
                status = 200
        else:
            code = str(raw.get("error_code", "handshake"))
            status = {"dns": 404, "private": 403}.get(code, 502)
            payload = {"error": code, "detail": str(raw["error"]), "domain": d}
        cache_put(d, payload, status)
        return JSONResponse(payload, status_code=status)
