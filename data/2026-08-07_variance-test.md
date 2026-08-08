# Phase 4 variance test, 2026-08-07

Question: does measured per-cert content materially beat the constant-delta
model? Answer, recorded before anyone was attached to it: mostly no at the
verdict level, with two specific things surviving. Output below; the
interpretation lives in the article draft and scope. All figures Proposed.

```

=== ML-DSA-44, full-chain migration, classical SCTs ===
measured-content: p50=16,810 p95=21,499
  B1-EC  vs IW10: false-pass 0 (0.0%), false-alarm 72 (0.9%)
  B1-EC  vs IW20: false-pass 0 (0.0%), false-alarm 18 (0.2%)
  B1-EC  model p50=18,268 p95=24,212; deviation (measured - model) p5=-2,572 p50=-1,161 p95=-242
  A (literature-only, EC-typical) p50=15,856
  B1-RSA vs IW10: false-pass 14 (0.2%), false-alarm 0 (0.0%)
  B1-RSA vs IW20: false-pass 0 (0.0%), false-alarm 0 (0.0%)
  B1-RSA model p50=17,107 p95=22,723; deviation (measured - model) p5=-1,280 p50=0 p95=927
  A (literature-only, RSA-typical) p50=14,981

=== ML-DSA-65, full-chain migration, classical SCTs ===
measured-content: p50=22,282 p95=28,495
  B1-EC  vs IW10: false-pass 0 (0.0%), false-alarm 0 (0.0%)
  B1-EC  vs IW20: false-pass 0 (0.0%), false-alarm 462 (5.7%)
  B1-EC  model p50=23,743 p95=31,164; deviation (measured - model) p5=-2,572 p50=-1,161 p95=-242
  A (literature-only, EC-typical) p50=20,202
  B1-RSA vs IW10: false-pass 0 (0.0%), false-alarm 0 (0.0%)
  B1-RSA vs IW20: false-pass 17 (0.2%), false-alarm 361 (4.4%)
  B1-RSA model p50=22,582 p95=29,626; deviation (measured - model) p5=-1,280 p50=0 p95=927
  A (literature-only, RSA-typical) p50=19,327

=== SCT migration scenario: constant SCT-count assumption vs measured (ML-DSA-44, full) ===
  assume every site has 2 SCTs: 72 IW20 verdict flips (0.9%)
  assume every site has 3 SCTs: 44 IW20 verdict flips (0.5%)

domains tested: 8151
```
