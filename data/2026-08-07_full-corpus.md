# Full-corpus run of record, 2026-08-07

Capture complete: 10,000 Tranco ZJGPG domains attempted, 8,152 chains
captured (81.5%). Raw evidence: data/raw/capture-top10k.jsonl (local).
Derived dataset: data/summary-top10k.jsonl. All projection figures are
Proposed (assumptions: src/project_chains.py docstring). Supersedes the
84% checkpoint in data/checkpoints/.

## Corpus statistics

```
records=10000 ok=8152 (81.5% success)

served chain bytes: p5=2456 p50=3754 p95=6465 max=14565
  Reported baseline (cert-abridge, Tranco): p5/p50/p95 = (2308, 4032, 5609)

served depth: {1: 43, 2: 1260, 3: 5581, 4: 1222, 5: 35, 6: 6, 7: 4, 9: 1}
ICA count: 0: 46 (0.6%), 1: 1861 (22.8%), 2: 5389 (66.1%), 3: 835 (10.2%), 4: 15 (0.2%), 5: 4 (0.0%), 6: 1 (0.0%), 7: 1 (0.0%)
  Reported baseline (Sikeridis 2022): 0 ICA 13-31%, 1 ICA 35-45%, 2 ICA 24-30%, 3 ICA 9-12%
root transmitted: 1065 (13.1%)

leaf key alg: RSA: 4987 (61.2%), EC: 3164 (38.8%), ?: 1 (0.0%)
  Reported baseline (arXiv:2607.29005): RSA 56.9% / ECDSA 43.1%
leaf SCT count: {0: 23, 2: 3949, 3: 4117, 4: 34, 5: 25, 6: 1, 7: 3}
leaf SANs: p50=2 p95=52 max=447

size spread at fixed depth (the variance signal):
  depth 1: n=43 p5=789 p50=1676 p95=2517 p95/p5=3.19x
  depth 2: n=1260 p5=2289 p50=2986 p95=4570 p95/p5=2.0x
  depth 3: n=5581 p5=2457 p50=3788 p95=5269 p95/p5=2.14x
  depth 4: n=1222 p5=3380 p50=3443 p95=6886 p95/p5=2.04x
  depth 5: n=35 p5=4303 p50=7184 p95=8492 p95/p5=1.97x

failures: {'gaierror': 1439, 'TimeoutError': 242, 'SSLError': 118, 'OSError': 23, 'ConnectionRefusedError': 13, 'ConnectionResetError': 11, 'SSLEOFError': 2}
cert parse errors: 1
```

## Projection (Proposed)

```
projecting 8152 domains (PROPOSED figures; assumptions in module docstring)

scenario                                     p50 flight p95 flight   >IW10   >IW20  >amp3x
ML-DSA-44 scts=classical migration=full          16,810     21,499   85.1%    0.1%   99.9%
ML-DSA-44 scts=classical migration=leaf-only      8,506     11,176    0.3%    0.0%   66.3%
ML-DSA-44 scts=migrated migration=full           21,651     28,535   99.7%    1.6%   99.9%
ML-DSA-44 scts=migrated migration=leaf-only      14,565     18,272   48.7%    0.0%   99.8%
ML-DSA-65 scts=classical migration=full          22,282     28,495   99.5%    1.5%  100.0%
ML-DSA-65 scts=classical migration=leaf-only     10,035     12,705    0.9%    0.0%   99.2%
ML-DSA-65 scts=migrated migration=full           28,805     38,201   99.8%   48.1%  100.0%
ML-DSA-65 scts=migrated migration=leaf-only      18,717     22,456   99.7%    0.1%   99.8%
```
