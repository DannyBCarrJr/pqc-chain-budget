# pqc-chain-budget, project scope

Status: draft, 2026-08-07. Pre-measurement. Nothing here is public until the
claim-check pass runs and ePrint 2026/866 has been read in full (see
`../PRIOR-ART.md`, watch items).

## One line

Measure the real certificate chains of the Tranco top 10k, project each chain's
post-quantum equivalent from its own measured content, and report the projected
distribution and per-site verdicts against the TLS first-flight budget: a public
dataset, a free per-domain checker on carrdigital.dev, and an article.

## The research question

Every published PQ size projection applies a constant delta to a modeled chain.
The open empirical question: is per-site variance in chain composition (depth,
SCT count, SAN count, extension bloat, key sizes) large enough that the projected
distribution's tail differs materially from the constant-delta model built on
published depth distributions?

Both answers publish. Yes: a distributional finding nobody has measured. No: the
constant-delta model is validated against real chains for the first time anyone
has checked, and the dataset and tool stand on their own. This framing is the
project's defense against the "arithmetically trivial" objection recorded in
PRIOR-ART.md, and it is falsifiable, which is the point.

## What is claimed and what is cited

The exact permitted claim wording, its two mandatory traveling sentences, and the
full preemption map live in `../PRIOR-ART.md`. Summary of the boundary:

- Cited, never claimed: per-site real-chain analysis against a transport budget
  (Nawrocki, CoNEXT 2022), per-sample budget classification (Fastly 2024), the
  ML-DSA substitution arithmetic (Kampanakis and Childs-Klein 2024), the
  budget-verdict table by chain depth (Kampanakis and Kallitsis 2022), the
  real-chain aggregate PQ projection (Cloudflare 2024/2025).
- Claimed, narrowly: the join. Per-chain byte-level PQ projection computed from
  each site's own certificate content, reported as a weighted distribution and
  per-site verdicts against the flight budget.
- Banned words in every public artifact: "first", "only", "no one has".

## Method

### Phase 1: corpus capture (Verified tier)

1. Pin a Tranco list ID (reproducibility; the list ID goes in the dataset).
2. One TLS 1.3 connection per domain, no retries beyond one, polite pacing,
   honest User-Agent. Capture the full served chain in DER.
3. Record per domain: chain depth as served, per-certificate DER size, signature
   algorithm, key algorithm and size, SAN count, embedded SCT count, OCSP/CRL
   URLs, whether the root was transmitted, negotiated group (free adoption
   statistic as a by-product), certificate_compression advertisement.
4. Dedup into distinct chain shapes with population weights. The shape table is
   a first-class output; per-domain rows are a view over it. Compare the depth
   distribution against Sikeridis 2022/1556 as the published baseline.
5. Reproduce cert-abridge's classical p5/p50/p95 on this corpus before any
   projection, as the calibration check that the capture is sound.

### Phase 2: projection (Proposed tier, always)

Per certificate, replace the measured signature and public key bytes with FIPS
204 sizes for its position in the chain; everything else in the certificate
(DNs, SANs, extensions, SCT structure) keeps its measured size. Scenario axes,
never a single number:

- Parameter set: ML-DSA-44 and ML-DSA-65 (composite per draft-lamps as a
  stretch column).
- SCT migration: classical SCTs retained vs ML-DSA SCTs.
- Root on the wire: as observed per site (Delgado's depth-3 finding is an
  11,015-byte swing and cannot be assumed away).
- Intermediate migration: full chain vs leaf-only migration.

### Phase 3: verdict (Proposed tier)

Evaluate the FLIGHT, not the chain: projected Certificate message plus the
measured non-Certificate flight overhead from pqc-cert-matrix's per-message
attribution (3,680 bytes for ML-DSA-44 to 5,887 for ML-DSA-87). Window is a
scenario input, not a constant: IW10 (14,600 bytes) as the headline column, IW20
and IW32 alongside, because real CDNs commonly run larger windows and a bare
IW10 FAIL would be wrong for a large share of the corpus. Also compute the
QUIC 3x amplification verdict so the results are directly comparable to
Nawrocki.

### Phase 4: variance test (the research question)

Build the constant-delta model from published inputs only (Sikeridis depth
distribution, FIPS 204 deltas), then compare its projected distribution against
the measured-content projection. Report where and by how much the tails diverge,
with the divergence attributed to its cause (SCTs vs extension bloat vs depth).

## Deliverables

1. **Dataset and scripts**: this repo, public at release, MIT, every number
   regenerable by script, captured evidence ships. Zenodo DOI after v1.0.0,
   matching the pqc-cert-matrix pattern.
2. **The checker**: carrdigital.dev tool page. Corpus domains resolve from a
   precomputed static JSON (no backend, no drift from the dataset); the page
   states its assumptions and stamps every projected figure Proposed. Window
   selectable (IW10/IW20/IW32). Sits beside the handshake budget calculator.
3. **Article** on the carrdigital.dev writing section: the headline weighted
   percentage, the variance-test answer either way, Provenance section, full
   citations per PRIOR-ART.md.

## Constraints

- Claim discipline: every figure stamped Verified (measured chains), Reported
  (cited), or Proposed (projections, all of them). claim-check runs before
  anything ships.
- Read IACR ePrint 2026/866 in full before publication. Non-negotiable; it is
  the one unread near neighbor.
- Re-run the prior-art sweep immediately before publication (the 08-07 sweep
  was rate-limited on arXiv metadata; Red Sift is one sprint from shipping the
  same framing).
- Scanning etiquette: single connection per domain, no vulnerability probing,
  standard measurement-research practice. This is chain capture, the same act a
  browser performs.
- Prose follows `~/.rocky/steering/writing-style.md`. No em dashes, no banned
  vocabulary, sentence-case headings.
- Boundary: open tooling, no vendor accounts, no employer material, consistent
  with the 2026-08-01 strategy call (the evidence layer stays free).

## Open decisions for Danny

- Project and tool naming. `pqc-chain-budget` is the working name; renaming now
  is free, after the repo goes public it is not.
- Corpus size: top 10k is the working default. Top 100k roughly 10x's capture
  time for a stronger tail; decide before Phase 1 pins the Tranco ID.
- Whether the checker also accepts arbitrary (non-corpus) domains, which needs a
  live capture backend (Render or a Worker with TCP sockets) and is deliberately
  out of scope for v1.
