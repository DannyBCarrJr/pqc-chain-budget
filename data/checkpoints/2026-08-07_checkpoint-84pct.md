# Checkpoint: 84% of capture, 2026-08-07

Interim numbers recorded mid-capture: 8,650 of 10,000 domains attempted
(Tranco ZJGPG), 7,009 chains captured. The pending tail skews toward
failures, so distributions here are near-final but NOT the dataset of
record; the full-corpus run supersedes this file. All projection figures
are Proposed (assumptions: src/project_chains.py docstring).

## Corpus statistics

```
records=8650 ok=7009 (81.0% success)

served chain bytes: p5=2456 p50=3769 p95=6476 max=14565
  Reported baseline (cert-abridge, Tranco): p5/p50/p95 = (2308, 4032, 5609)

served depth: {1: 36, 2: 1135, 3: 4745, 4: 1052, 5: 31, 6: 6, 7: 3, 9: 1}
ICA count: 0: 39 (0.6%), 1: 1680 (24.0%), 2: 4556 (65.0%), 3: 716 (10.2%), 4: 13 (0.2%), 5: 3 (0.0%), 6: 1 (0.0%), 7: 1 (0.0%)
  Reported baseline (Sikeridis 2022): 0 ICA 13-31%, 1 ICA 35-45%, 2 ICA 24-30%, 3 ICA 9-12%
root transmitted: 950 (13.6%)

leaf key alg: RSA: 4450 (63.5%), EC: 2558 (36.5%), ?: 1 (0.0%)
  Reported baseline (arXiv:2607.29005): RSA 56.9% / ECDSA 43.1%
leaf SCT count: {0: 20, 2: 3217, 3: 3719, 4: 31, 5: 20, 6: 1, 7: 1}
leaf SANs: p50=2 p95=57 max=447

size spread at fixed depth (the variance signal):
  depth 1: n=36 p5=771 p50=1707 p95=4226 p95/p5=5.48x
  depth 2: n=1135 p5=2288 p50=2987 p95=4602 p95/p5=2.01x
  depth 3: n=4745 p5=2457 p50=3800 p95=5317 p95/p5=2.16x
  depth 4: n=1052 p5=3380 p50=3455 p95=6886 p95/p5=2.04x
  depth 5: n=31 p5=4303 p50=7567 p95=8492 p95/p5=1.97x

failures: {'gaierror': 1309, 'TimeoutError': 208, 'SSLError': 84, 'OSError': 15, 'ConnectionRefusedError': 13, 'ConnectionResetError': 10, 'SSLEOFError': 2}
cert parse errors: 1
```

## Projection (Proposed)

```
projecting 7009 domains (PROPOSED figures; assumptions in module docstring)

scenario                                     p50 flight p95 flight   >IW10   >IW20  >amp3x
ML-DSA-44 scts=classical migration=full          16,968     21,523   84.4%    0.1%   99.9%
ML-DSA-44 scts=classical migration=leaf-only      8,518     11,225    0.4%    0.0%   68.7%
ML-DSA-44 scts=migrated migration=full           22,171     28,541   99.8%    1.7%   99.9%
ML-DSA-44 scts=migrated migration=leaf-only      14,623     18,277   51.2%    0.0%   99.8%
ML-DSA-65 scts=classical migration=full          22,443     28,507   99.5%    1.6%  100.0%
ML-DSA-65 scts=classical migration=leaf-only     10,047     12,754    1.0%    0.0%   99.2%
ML-DSA-65 scts=migrated migration=full           29,217     38,206   99.8%   50.1%  100.0%
ML-DSA-65 scts=migrated migration=leaf-only      18,803     22,468   99.7%    0.1%   99.8%
```
