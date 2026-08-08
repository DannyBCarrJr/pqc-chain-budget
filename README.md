# pqc-chain-budget

Measured certificate chains of real websites, projected to their post-quantum
equivalents, evaluated against the TLS first-flight budget.

Status: pre-measurement draft, 2026-08-07. Private until the dataset exists and
the claim-check pass runs.

- `docs/scope.md`: what this project is, the research question, method, and
  deliverables.
- `PRIOR-ART.md`: governs every public claim. Read it before writing anything
  that leaves this repo. Seeded from a three-agent adversarial sweep on
  2026-08-07, before any code was written.
- `.sources/` (local only, gitignored): full texts of every prior-art source,
  preserved so citations are verified against papers, never summaries.

Sibling projects: [pqc-cert-matrix](https://github.com/DannyBCarrJr/pqc-cert-matrix)
(measured client-stack compatibility, the source of the flight-budget numbers this
project builds on) and
[post-quantum-measured-lab](https://github.com/DannyBCarrJr/post-quantum-measured-lab).
