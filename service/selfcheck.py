#!/usr/bin/env python3
"""Self-check for the live checker: the smallest thing that fails if the
logic breaks. Plain asserts, no framework. Offline checks always run;
`--live` adds one real handshake and verifies the full pipeline against a
recomputation. Run from service/: python selfcheck.py [--live]
"""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import app
from app import build_payload, measure, normalize, over_budget, resolve_global
from export_web import SCENARIOS
from project_chains import project_domain
from parse_chains import summarize

# --- normalize: page-mirroring plus the stricter socket-side rules ---
assert normalize("https://Example.COM/path?q=1") == "example.com"
assert normalize("www.example.com.") == "example.com"
assert normalize("example.com:8443") == "example.com"
assert normalize("bücher.example") == "xn--bcher-kva.example"
assert normalize("192.0.2.7") is None, "IPv4 literal must be refused"
assert normalize("[2001:db8::1]") is None, "IPv6 literal must be refused"
assert normalize("localhost") is None, "single label must be refused"
assert normalize("-bad-.example.com") is None
assert normalize("") is None
assert normalize("a" * 260 + ".com") is None

# --- vetting: only globally routable addresses survive ---
def fake_gai(addrs):
    def gai(host, port, proto=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, 443)) for a in addrs]
    return gai

_real_gai = socket.getaddrinfo
try:
    socket.getaddrinfo = fake_gai(["127.0.0.1", "10.0.0.5", "169.254.169.254", "100.64.0.1"])
    addrs, resolved = resolve_global("whatever.example")
    assert resolved and addrs == [], f"private/link-local/CGNAT must be vetted out, got {addrs}"
    socket.getaddrinfo = fake_gai(["93.184.216.34", "10.0.0.5", "93.184.216.34"])
    addrs, _ = resolve_global("whatever.example")
    assert addrs == ["93.184.216.34"], f"expected the one global address deduped, got {addrs}"
    def boom(*a, **k):
        raise socket.gaierror("no such name")
    socket.getaddrinfo = boom
    addrs, resolved = resolve_global("whatever.example")
    assert not resolved and addrs == []
finally:
    socket.getaddrinfo = _real_gai

# --- scenario order: the live flights array must line up with the deployed
# page data, which indexes flights by meta.json's scenario list ---
meta = json.loads((Path(__file__).resolve().parent.parent / "data/web-export/meta.json").read_text())
assert [f"{p}|{s}|{m}" for p, s, m in SCENARIOS] == meta["scenarios"], (
    "SCENARIOS order drifted from the shipped meta.json; live rows would render wrong"
)

# --- budget: trips exactly at the limit ---
app._hits.clear()
assert all(not over_budget("t") for _ in range(app.BUDGET_PER_HOUR))
assert over_budget("t"), "budget must trip after BUDGET_PER_HOUR hits"
assert not over_budget("someone-else")
app._hits.clear()

# --- budget dict: stale buckets purge once the dict is large ---
import collections
import time as _time
_stale = _time.monotonic() - 7200
for i in range(10_001):
    app._hits[f"spoof-{i}"] = collections.deque([_stale])
over_budget("fresh")
assert len(app._hits) <= 2, (
    f"stale _hits buckets survived the purge: {len(app._hits)} left; "
    "unique spoofed client headers would grow the dict forever"
)
app._hits.clear()

# --- cache eviction: stays bounded ---
app._cache.clear()
_max = app.CACHE_MAX
app.CACHE_MAX = 5
try:
    for i in range(12):
        app.cache_put(f"d{i}.example", {"ok": i}, 200)
    assert len(app._cache) <= 5, f"cache exceeded its bound: {len(app._cache)}"
finally:
    app.CACHE_MAX = _max
    app._cache.clear()

print("offline self-check: OK")

if "--live" in sys.argv:
    raw = measure("example.com")
    assert raw["ok"], f"live handshake failed: {raw}"
    payload = build_payload(raw)
    assert payload is not None, "live capture did not build a payload"
    row = payload["row"]
    assert row[0] is None and len(row) == 7 and len(row[6]) == len(SCENARIOS), f"row shape wrong: {row}"
    assert payload["scenarios"] == [f"{p}|{s}|{m}" for p, s, m in SCENARIOS]
    assert len(payload["certs"]) == row[2] == len(payload["certs_der_b64"]), (
        "evidence must carry one parsed-fact entry and one DER per certificate"
    )
    assert all(c["der_len"] and c["sig_len"] and c["spki_len"] for c in payload["certs"])
    # The flights must equal an independent recomputation through the
    # published projection, in meta.json scenario order.
    rec = summarize(raw)
    expected = [project_domain(rec, p, s, m)["projected_flight"] for p, s, m in SCENARIOS]
    assert row[6] == expected, "live flights disagree with direct projection"
    assert row[1] == rec["total_der_bytes"] and row[2] == rec["depth"]
    print(f"live self-check: OK ({payload['hostname']}, {row[2]} certs, {row[1]} DER bytes, "
          f"flights {row[6][0]}..{row[6][-1]})")
