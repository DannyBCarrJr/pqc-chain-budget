# pqc-chain-budget

Measured certificate chains of real websites, projected to their post-quantum equivalents, evaluated against the TLS server's first-flight budget. Every number regenerable by script; the captured evidence ships in this repo.

Written up: [The typical chain moved](https://carrdigital.dev/writing/the-typical-chain-moved/)
and [The same 985 bytes](https://carrdigital.dev/writing/the-same-985-bytes/) (certificate compression).
Interactive per-domain lookup: [chain check](https://carrdigital.dev/tools/chain-check/).
Cite the concept DOI [10.5281/zenodo.21846142](https://doi.org/10.5281/zenodo.21846142)
(resolves to the latest version; v1.0.0 is pinned by 10.5281/zenodo.21846143).

## Headline results

All projections are stamped **Proposed**: arithmetic on measured inputs under
stated assumptions, never a measurement of a post-quantum handshake. The input
chains are **Verified**: captured 2026-08-07, Tranco list ZJGPG, 8,152 of the
top 10,000 domains completed a handshake, 8,151 parseable.

- Under a drop-in ML-DSA-44 migration (full chain, SCTs classical), **85.1% of
  measured sites project past the IW10 initial congestion window**, an extra
  round trip per full handshake. The direction was predicted by typical-chain
  models; the fraction, the spread, and the per-site verdicts are what this
  corpus adds.
- **Leaf-only migration fits almost everywhere**: 0.3% (ML-DSA-44) and 0.9%
  (ML-DSA-65) of sites exceed IW10.
- **Unless CT logs go hash-based.** If each embedded SCT carries an
  SLH-DSA-128s signature (7,856 bytes, measured with OpenSSL 3.5.5), the SCTs
  alone outweigh the certificates: even leaf-only migration projects past
  IW10 for 99.7% of sites, and past IW20 for 51.6%. Added 2026-08-19 as a
  third SCT scenario; the eight original scenarios are unchanged.
- **Certificate compression recovers a median 985 bytes (28.6%) on these chains
  today, and roughly the same 985 bytes after migration**, which is 7.4% of an
  ML-DSA-44 chain and 5.5% of an ML-DSA-65 one. The saving is structural, and
  migration adds no structure. That compression does not rescue post-quantum
  certificates is stated in two IETF drafts and is cited, never claimed here;
  measuring compression across a large corpus of real chains is also published
  work (cert-abridge, ~75,000 chains). See `PRIOR-ART.md` before repeating any
  of this.
- If CT log signatures migrate to ML-DSA-65 with the chains, **48.1% of sites
  project past even IW20**.
- The corpus is 2-intermediate dominant (66.1% under the counting rule stated
  in the article), against one-intermediate typical chains in most models and
  a 2022 published baseline whose comparability is partly definitional.
- A constant-delta model with fresh corpus inputs reproduces these verdicts
  almost exactly (worst case 5.7% flips); built purely from published inputs it
  lands 1 to 1.8KB light at the median. The arithmetic was fine. The inputs
  were stale.
- Side observations: 13.1% of sites transmit their root; 54.7% of a 1,019-site
  subsample negotiates X25519MLKEM768 with an OpenSSL 3.5.5 default client;
  284 of 285 classical TLS 1.3 servers answered that client's single hybrid
  key share with a HelloRetryRequest (RFC 8446 working as specified).

`PRIOR-ART.md` governs every claim, records what published work already covers,
and names what to cite. Read it before quoting anything here as new.

## Layout

- `src/capture_chains.py`: evidence-only capture, one connection per domain.
- `src/parse_chains.py`: offline derivation from raw capture. No network.
- `src/corpus_stats.py`: Phase 1 statistics with published baselines inline.
- `src/project_chains.py`: the projection model and its assumptions.
- `src/variance_test.py`: the constant-delta comparison (Phase 4).
- `src/probe_groups.py`: negotiated-group and HRR subsample via s_client.
- `src/compress_chains.py`: RFC 8879 compression on the captured chains, its
  decomposition, and the same saving carried onto the migrated chain.
- `src/export_web.py`: static data for the chain check tool.
- `service/`: the live half of the chain check tool. One handshake for any
  public domain not in the corpus, through the same capture, parse, and
  projection code imported from `src/`, returned in the corpus row shape.
  Guardrails and run instructions in `service/README.md`.
- `scripts/fetch-corpus.sh`: pins and downloads the Tranco corpus.
- `scripts/measure-mldsa-sizes.sh`: regenerates the ML-DSA size constants.
- `data/capture-top10k.jsonl.gz`: the raw captured evidence (chains as served,
  base64 DER). `data/summary-top10k.jsonl`: the parsed dataset.
  `data/2026-08-07_*.md`: dated records of each analysis run.

## Reproduce

```bash
# re-derive everything from the shipped evidence, no network needed
gunzip -k data/capture-top10k.jsonl.gz
python3 src/parse_chains.py --input data/capture-top10k.jsonl --output /tmp/summary.jsonl
python3 src/corpus_stats.py --input /tmp/summary.jsonl
python3 src/project_chains.py --input /tmp/summary.jsonl

# or capture a fresh corpus (the numbers will drift as chains rotate)
./scripts/fetch-corpus.sh
python3 src/capture_chains.py --input data/corpus-top10k.csv --output /tmp/capture.jsonl
```

Requires Python 3.13+ (for `ssl.SSLSocket.get_unverified_chain`) and the
`cryptography` package. The probe subsample additionally requires OpenSSL 3.5+.

## Sibling projects

[pqc-cert-matrix](https://github.com/DannyBCarrJr/pqc-cert-matrix) (measured
client-stack compatibility; source of the flight-budget constants) and
[post-quantum-measured-lab](https://github.com/DannyBCarrJr/post-quantum-measured-lab)
(the book's public lab).

MIT license. If a number here disagrees when you rerun it, open an issue.
