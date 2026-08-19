# Live chain check service

The corpus tool at [carrdigital.dev/tools/chain-check](https://carrdigital.dev/tools/chain-check/)
answers from a static snapshot of the Tranco top 10k. This service answers for
any other public domain: one handshake, then the same parse and projection the
corpus went through, returned in the corpus row shape so the page renders both
identically. The measurement code is imported from `../src/`, never copied, so
the live path cannot drift from the published method. Live chain facts are
measured at request time; every projected figure stays **Proposed** under the
assumptions in `project_chains.py`.

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python selfcheck.py --live   # asserts the pipeline against a recomputation
.venv/bin/uvicorn app:app --port 8000
curl 'http://127.0.0.1:8000/check?domain=example.com'
```

Python 3.13+ is required (`ssl.get_unverified_chain`). The Dockerfile builds
from the repo root: `docker build -f service/Dockerfile .`

## API

- `GET /check?domain=<hostname>` returns `{domain, hostname, ts, tls_version,
  row}` where `row` matches `export_web.py`'s `row_fields` with `rank` null.
  Errors: 400 not a hostname, 403 resolves only to non-public addresses,
  404 does not resolve, 429 over budget, 502 handshake or parse failure.
- `GET /healthz` reports the interpreter and OpenSSL versions doing the measuring.

## Guardrails

"Measure any host" is an SSRF primitive if left bare, so: hostnames only
(never IP literals), port fixed at 443, every resolved address vetted and only
globally routable ones dialed, and the connection pins the vetted address so a
second resolution cannot rebind somewhere private. A per-client hourly budget
(`BUDGET_PER_HOUR`, default 20), a global concurrency cap (`MAX_CONCURRENT`,
default 4), and a result cache (24h success, 10 min failure) keep the service
from being repurposed as a scanner. Rate identity comes from
`CF-Connecting-IP` or the first `X-Forwarded-For` hop and is abuse damping,
not a security boundary; the hard ceilings are the semaphore and the cache.

Config is environment variables, all optional: `ALLOW_ORIGINS` (CORS, default
`https://carrdigital.dev`), plus the knobs named above and the cache TTLs in
`app.py`.
