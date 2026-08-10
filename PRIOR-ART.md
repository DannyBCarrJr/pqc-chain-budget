# Prior art, per claim

Seeded 2026-08-07 from a three-agent adversarial sweep run before any code was
written. Full texts of every source below are preserved locally in `.sources/`
(gitignored; third-party copyrighted material never ships in this repo). Verdicts
are conservative on purpose. Anything marked PREEMPTED must be cited, never
claimed. The style rules of `pqc-cert-matrix/PRIOR-ART.md` apply here unchanged:
the words "first", "only", and "no one has" are banned from every public artifact
of this project. The only defensible form is "has not been published, as far as we
could find after searching X".

## The claim this project may make, verbatim

> We found no prior study that projects post-quantum signature sizes onto each
> site's own deployed certificate chain across a large corpus of real domains. The
> closest published work splits along two lines. Nawrocki et al. (CoNEXT 2022,
> arXiv:2211.02421) measure real per-site chains across more than 1M domains
> against a first-flight transport budget, QUIC's 3x amplification limit, and
> report that 35% of server certificates exceed it, but they analyze classical
> certificates only. Kampanakis and Childs-Klein (MADWeb 2024), Kampanakis and
> Lepoint (SSR 2023), and Chou and Cao (arXiv:2604.24869) all run the post-quantum
> size against first-flight analysis, but on a single constructed "typical" chain
> or a synthetic size sweep rather than on deployed chains. This work joins the
> two.

Two sentences travel with that claim permanently, or the caveats below become the
rebuttal:

> Because a top-N corpus is concentrated in a few issuers and CDNs, we report
> distinct chain shapes with population weights rather than treating each domain
> as independent. The substitution is a projection under stated assumptions about
> parameter set, intermediate and SCT migration, and chain depth, so every figure
> here is stamped Proposed, not Verified, even though the input chains are
> measured.

## The claim the tool may make, verbatim

> Searched 2026-08-07. Every free per-domain post-quantum checker we could find
> answers one question: does this site negotiate a post-quantum key exchange
> today. DigiCert's PQC checker, Wiz's PQC tester, QuReady, KF-Cipher and Pinaka
> all stop there; PostQ goes one step further and reports the chain's public-key
> and signature algorithms. None of them projects what that chain will weigh once
> ML-DSA or a composite signs it, and none checks the projection against the
> server's first flight. That gap is what this tool fills.
>
> The constraint itself is not new and is not claimed here. Kampanakis and
> Childs-Klein (ePrint 2024/176) identified Certificate and CertificateVerify as
> the largest handshake messages and discussed tuning initcwnd; Chou and Cao
> (arXiv:2604.24869) measured certificate chain size against the 14KB initial
> window. What this adds is per-domain application and a flight-level budget
> rather than a chain-level one, which is roughly one signature stricter.

## The claim the compression work may make, verbatim

Added 2026-08-09. This one is narrow, and it is narrow because the sweep cut it
down twice. Read the whole section before writing a word about compression.

> Certificate compression on real chains is measured work, not ours: Jackson's
> abridged-certs draft evaluated ~75,000 Tranco chains and published percentiles
> for ZStandard at maximum parameters. The conclusion that it does not rescue
> post-quantum certificates is also not ours; it is stated in that draft and in
> draft-ietf-uta-pqc-app-03, both quoted below. What this work adds is the
> decomposition of the saving into its within-certificate and cross-certificate
> parts, the observation that brotli beats zstd on 87.4% of these chains, and
> the join to this repo's per-site projection: the same measured saving carried
> onto each site's own migrated chain.

**PREEMPTED, and this is the sentence that gets the repo in trouble if it is
softened.** `draft-ietf-tls-cert-abridge-02` Table 1 reports p5/p50/p95 of 2308 /
4032 / 5609 uncompressed and 1619 / 3243 / 3821 compressed over ~75,000 Tranco
chains. The caption states the row "used ZStandard with the parameters configured
for maximum compression". Verified by downloading the draft and reading Table 1
with its caption, 2026-08-09. **Measuring certificate compression over a large
corpus of real WebPKI chains is published work. Never present it as new.** Our
corpus is 8,152 chains, roughly a ninth the size.

**PREEMPTED, qualitative post-quantum conclusion, twice.** Verified verbatim
2026-08-09 by downloading both drafts:

- `draft-ietf-tls-cert-abridge-02`, lines 141-146: post-quantum signatures and
  keys "will be typically 10 to 40 times their current size and cannot be
  compressed with existing TLS Certificate Compression schemes because most of
  the size of the certificate is in high entropy fields such as cryptographic
  keys and signatures."
- `draft-ietf-uta-pqc-app-03`, lines 864-870: "While effective in many scenarios,
  its impact on PQ or PQ/T hybrid certificates is limited due to the larger sizes
  of public keys and signatures in PQC. These high-entropy fields, inherent to
  PQC algorithms, constrain the overall compression effectiveness."

**Open, as far as we could find after searching.** Neither draft, and no source
found, publishes the post-migration compression percentage on real chains.
cert-abridge cites Westerbaan's "Sizing Up Post-Quantum Signatures" for
post-quantum sizing; that post does not discuss certificate compression at all
(checked 2026-08-09). arXiv:2604.06100 contains one instance of the word
"compress" and it is metaphorical. arXiv:2606.16473 contains none.

**Demoted before publication.** The 4-byte expansion of ML-DSA fields under
every RFC 8879 algorithm is measured and reproducible, and it is also the
expected behavior of a compressor given incompressible input. It ships as an
illustration of the drafts' claim. It is not a finding and must not be written
as one.

**Not a deployment survey, and must never be dressed as one (added 2026-08-10).**
The subsample records that 3 of 842 TLS 1.3 servers negotiated a live
CompressedCertificate. Verified, and correct for what it is: a byproduct of a
1,019-host probe run for negotiated groups. It is not a measurement of how much
of the web deploys RFC 8879. The sample is one eighth of the corpus by rank
stride, all three hits are Meta properties, and four more Meta hosts that also
compress fell outside the sample, so the figure is known to undercount by an
unmeasured amount. It is also client-relative: this build offers zlib and zstd
only. Before any prevalence claim is written from this number, search the prior
art properly, because live compression deployment is a well-trodden measurement
area and nothing here was designed to survey it. Evidence and method:
`data/2026-08-10_compression-verification.md`.

## PREEMPTED, cite instead of claim

**The methodology, classical half: Nawrocki, Tehrani, Hiesgen, Mücke, Schmidt,
Wählisch, "On the Interplay between TLS Certificates and QUIC Performance",
CoNEXT 2022 (arXiv:2211.02421).** The nearest prior art to this entire project.
Over 1M Web domains, 272k QUIC-enabled services, real deployed chains, evaluated
per-site against a first-flight transport byte budget (the QUIC 3x amplification
limit): "sizes of 35% of server certificates exceed the amplification limit."
Median chain 2,329 bytes for QUIC domains, 4,022 for others. Verified by grep of
the full text: zero occurrences of "quantum", "post-quantum", "ML-DSA",
"Dilithium", "Kyber". Our method is their method with a signature substitution.
Cite them everywhere the method appears.

**The methodology, budget-classification half: Fastly (Patrick McManus), "Does
the QUIC handshake require compression to be fast?", 2024-12-06.** ~125,000 real
handshakes sampled from 9 cities on 6 continents, each classified against a
computed budget: "fits under budget even without compression, needs compression to
fit within budget, or never fits within budget," with a per-connection budget of
3,333 to 4,356 bytes. Verified by grep: zero occurrences of "quantum", "ML-DSA",
"Dilithium". The three-bucket per-sample classification is theirs; cite it.

**The substitution arithmetic: Kampanakis and Childs-Klein (AWS), "The impact of
data-heavy, post-quantum TLS 1.3 on the Time-To-Last-Byte", ePrint 2024/176,
MADWeb 2024.** Owns the ML-DSA drop-in arithmetic on a typical chain, with
numbers: "That would amount to ~14 and ~19KB of 'TLS 1.3 authentication data' on
the wire for ML-DSA-44 and ML-DSA-65 respectively." Also owns "post-quantum
handshakes interact badly with the initial congestion window" (they explicitly
explore tuning initcwnd), and has since 2024. Their chains are synthetic:
"constructed using RSA, not ML-DSA certificates", sized 2.5KB / 8KB / 16KB by
hand.

**The budget-verdict table by chain depth: Kampanakis and Kallitsis, "Faster
Post-Quantum TLS Handshakes Without Intermediate CA Certificates", CSCML 2022.**
Their Table 1 is the closest published artifact to this project's output table:
PQ authentication data by ICA count across Dilithium/Falcon/Rainbow/SPHINCS+, in
three profiles (no SCTs, with SCTs, with SCTs and OCSP), color-coded against the
window: "Dilithium ... remains below ~14.5KB, the most commonly used TCP initcwnd
used today (10MSS), only for its Dilithium-2 parameter set for two or more ICAs";
"we would like to minimize this data to 9-10KB (in green)". Chain shape comes from
real Censys scans of Alexa and Umbrella Top 1M, but certificate content is a
parametric model with an assumed constant byte allowance per certificate.
Granularity is by ICA count, never by site. The gap we fill is measured per-site
content; the budget-verdict framing is theirs.

**Real-chain aggregate joined to a PQ projection: Cloudflare (Westerbaan and
Valenta), "A look at the latest post-quantum signature standardization
candidates" (2024-11-07), repeated in "State of the post-quantum Internet in
2025" (2025-10-28).** "The median certificate chain today (with compression) is
3.2kB ... For the majority of QUIC connections, using ML-DSA as a drop-in
replacement for classical signatures would more than double the number of
transmitted bytes over the lifetime of the connection." Real chains, production
fleet, one median, no per-site resolution, no transport-limit verdict. This
sentence alone kills any "no one has projected PQ sizes on real chains" claim.

**PQ data-volume extrapolation over a real corpus: Sikeridis, Huntley, Ott,
Devetsikiotis, "Intermediate Certificate Suppression in Post-Quantum TLS", IACR
ePrint 2022/1556, CoNEXT 2022.** Tranco Top 10K chains collected monthly Jan to
Jun 2022, with the chain-depth distribution published (13 to 31% with 0 ICAs, 35
to 45% with 1, 24 to 30% with 2, 9 to 12% with 3), plus a Top 1M browsing
simulation. Their projection is aggregate data volume ("ICA suppression can save
~15MB in exchanged PQ authentication data for Dilithium III"), not per-site and
not a budget verdict. Their depth distribution is also the published baseline our
corpus stats will be compared against.

**Per-site framing on real sites with a PQ delta: Kampanakis and Anastasova,
"How much will ML-DSA affect Web Page Metrics?", PKI Consortium PQC Conference,
Austin, 2025-01.** 15 real, named top websites measured through webpagetest.org
with a constant +15KB (and +10KB "trimmed") PQ delta applied, reporting TTFB,
FCP, LCP under three network profiles. The per-site presentation on real sites
exists in public, from AWS. Their delta is a constant, not derived from each
site's own chain; that derivation is our contribution, and only that.

## Typical-chain PQ arithmetic (the tradition our projection refines)

All of these publish PQ size arithmetic on a modeled chain, none on a corpus:

- Westerbaan, "Sizing Up Post-Quantum Signatures", Cloudflare, 2021-11-08. Six
  signatures, two public keys; synthetic 1kB dummy certificates for the transport
  experiment; conclusion "easiest if six signatures and two public keys would fit
  in 9kB".
- Cloudflare, "The state of the post-quantum Internet", 2024-03-05: "It will take
  17kB extra to swap in ML-DSA-44."
- David Adrian, "Post-quantum cryptography is too damn big.", 2024-03-22:
  "5*2420 + 2*1312 = 14,724 bytes of signatures and public keys", a synthetic
  typical chain.
- draft-davidben-tls-merkle-tree-certs, section 1.1: "two SCTs and a leaf
  certificate signature adds 7,260 bytes ... with ML-DSA-44 and 9,927 bytes with
  ML-DSA-65." Model, no corpus.
- Let's Encrypt, "A Post-Quantum Future for Let's Encrypt", 2026-06-03: typical
  handshake "well past 10 kilobytes" under ML-DSA. Model.
- Kampanakis and Lepoint, SSR 2023 (ePrint 2023/266): post-quantum amplification
  factors "5 to 20 in typical settings". Typical settings, no corpus.
- Chou and Cao, arXiv:2604.24869: synthetic size sweep 4KB to 80KB via padded
  extensions ("artificially simulating their sizes by padding with certificate
  extensions"); real-world data is Zeek resumption-rate metadata, not
  certificates. Verified: zero hits for Tranco, Alexa, crawl, CT log, per-site.

## Checked and confirmed not preempting

- **arXiv:2607.29005 "Mind the Gap"** (1M domains, longitudinal): key-exchange
  adoption only. Zero hits for projection, initcwnd, flight, chain size,
  certificate size. Certificate analysis is hygiene (expiration, hostname
  mismatch). Only byte figure is observed ClientHello growth (median 1,176
  bytes).
- **arXiv:2606.16473 Dubey and Varshney** (32,011 domains): adoption counts only.
  Zero hits for congestion, flight, SCT, depth, intermediate. Provides the best
  framing statistic (49.3% hybrid KEX, 0% PQ certificates) and the CDN
  concentration figure (Cloudflare 37.97%).
- **draft-ietf-tls-cert-abridge-02**: publishes p5/p50/p95 (2,308 / 4,032 / 5,609
  bytes) over ~75,000 Tranco chains, classical only; cites Westerbaan 2021 for PQ
  sizes rather than projecting its own distribution. The projection of their own
  distribution is unclaimed, and their table is the classical baseline to
  reproduce before projecting.
- **Delgado Jiménez, arXiv:2604.06100 and arXiv:2605.02978**: lab-minted chains
  and a 250-target observability framework; "projection" in his text means policy
  projection, zero byte-level hits. His depth-3 finding (the root leaves the
  transmitted set, an 11,015-byte swing) is a required scenario axis in our
  projection model.
- **Astrizi and Custódio, "Seamless Transition to Post-Quantum TLS 1.3: A Hybrid
  Approach Using Identity-Based Encryption", *Sensors* 24(22):7300, 2024-11-15,
  DOI 10.3390/s24227300, PMID 39599077. Added 2026-08-10. Stamp: Reported,
  downloaded and grepped locally (`.sources/papers/`), not read via summary.**
  A KEMTLS variant using identity-based encryption so that existing classical
  certificates can be reused, with a proof-of-concept and a handshake size and
  latency comparison.

  **Does not preempt.** Verbatim from section 4: "The same certificate chain,
  sized at 2050 bytes, was used for all protocols except KEMTLS-IBE-PDK". One
  constructed chain, same class as Kampanakis and as Chou and Cao, which is
  precisely the line our corpus claim draws. Grepped for tranco, crawl, corpus,
  and any "N domains" pattern: the sole "Alexa" hit is a person's name in the
  acknowledgments. There is no deployed-chain corpus in the paper.

  **Cite it anyway** in any discussion of reducing chain weight, because reusing
  classical certificates is a different lever on the same budget than compression
  or leaf-only substitution.

- **METHODOLOGY GAP, found 2026-08-10 and applies to every claim in this file.**
  The paper above is squarely on topic, was published 2024-11-15, and the sweep
  of 2026-08-07 missed it. The reason is venue: that sweep covered arXiv, IACR
  ePrint, the IETF Datatracker, ETSI, BSI, and the ACM, IEEE, and USENIX
  proceedings. It did not cover **MDPI journals or PubMed Central**. MDPI's
  *Sensors*, *Entropy*, *Applied Sciences*, *Electronics*, *Mathematics*, and
  *Cryptography* publish post-quantum work steadily, *Scientific Reports* does
  too, and PMC indexes them. None of that surfaces in a search scoped to the
  venues above.

  **Consequence:** every "we found no published X, searching [list] on [date]"
  sentence in this repo and in `pqc-cert-matrix` currently rests on a search that
  omitted a whole publishing ecosystem. Add PMC and MDPI to the search list, name
  them in the scope sentence, and re-run before the next publication. A reviewer
  who finds an MDPI paper we missed damages the claim more than the paper itself
  ever would.

- **Tool landscape (opened 2026-08-07):** PostQ (postq.dev, free, reports current
  chain algorithms per domain, the deepest free checker found), DigiCert PQC
  checker, Wiz PQC tester, QuReady, KF-Cipher, Pinaka, PQCClear (login-walled
  questionnaire platform), SSL Labs (no PQC content), pq.cloudflareresearch.com
  (tests the browser, not a target domain), Keyfactor PQC Lab and Sectigo Quantum
  Labs (issuance sandboxes), anvilsecure/pqcscan (algorithm support only). None
  projects migration sizes against a transport budget. GitHub code searches for
  the combination ("14600" with "ML-DSA", "initial congestion window" with
  "ML-DSA") returned only this project's sibling repos.
- **Tenable, added 2026-08-10. Stamp: Reported.** Enterprise vulnerability
  management now ships post-quantum inventory, which puts this question inside
  the tool large organizations already run rather than in a free per-domain
  checker. Three Nessus plugins, all published **2025-12-08**, so this predates
  our work and is market context rather than a response to it.

  **Method:** the three plugin pages were downloaded with curl and the text
  extracted and grepped locally, not read through a summarizer. Raw HTML in
  `.sources/tenable/`. The originating announcement on connect.tenable.com is
  session-gated and **was not read**.

  | Plugin | Name | NASL | Version | Published / Updated |
  |---|---|---|---|---|
  | 277652 | Target Cipher Inventory | `target_cipher_inventory.nasl` | 1.5 | 2025-12-08 / 2026-04-13 |
  | 277653 | Remote Services Using Post-Quantum Ciphers | `services_using_post_quantum_crypto.nasl` | 1.1 | 2025-12-08 |
  | 277650 | Remote Services Not Using Post-Quantum Ciphers | | | 2025-12-08 |

  **Tenable declines the security conclusion in both directions, in its own
  words.** 277653: "This plugin reports network services that offer post-quantum
  ciphers and enumerates the post-quantum ciphers that they offer. Tenable makes
  no attempt to determine whether the remote service is actually hardened against
  a post-quantum attack." 277650: "Tenable makes no attempt to determine whether
  the remote service would be vulnerable to a post-quantum attack."

  **Tenable is being accurate and the disclaimer is good practice. Do not write
  this up as a vendor defect.** The gap is between what the plugin states and
  what a dashboard row labelled "Services Using Post-Quantum Ciphers" invites a
  reader to conclude, and the disclaimer lives in a plugin description almost no
  dashboard consumer opens. Same shape as the cert-matrix false-pass finding, at
  fleet scale, stated by the vendor rather than by us.

  **It does not touch the tool claim above.** That claim is scoped to free
  per-domain checkers, and this is neither free nor per-domain. Tenable projects
  no migration sizes and checks nothing against a transport budget.

  **Still UNVERIFIED, and worth settling before this appears in an article:**
  whether the 277652 JSON inventory covers certificate signature algorithms or
  only cipher suites and key exchange groups. Two pieces of support, neither
  conclusive. 277652 says "ciphers and algorithms" without distinguishing. And
  277650's own worked examples are "RSA asymmetric encryption and Diffie-Hellman
  key exchange", both confidentiality primitives, with no signature algorithm
  named anywhere in the three descriptions. TLS 1.3 cipher suites are AEAD-only,
  so "post-quantum cipher" most likely means the negotiated group. **That remains
  an inference from how TLS 1.3 works plus Tenable's choice of examples, not a
  statement in Tenable's text.** One look at the JSON attachment settles it.

## Watch items

- **IACR ePrint 2026/866: READ IN FULL 2026-08-07, does not preempt.** Danny
  retrieved the PDF past the 403 (`.sources/papers/2026-866.pdf`); converted
  and grepped. Zero occurrences of: congestion, initcwnd, flight,
  amplification, Tranco, "chain size", "certificate size", per-site,
  per-domain, and the word "bytes" appears zero times in the paper. Its
  "projection" is policy projection (readiness verdicts), its "budget" is
  probe-execution budget, and its 1000-target campaign measures hybrid KEX
  capability (310 targets confirmed) and collects 1,368 chain artifacts
  without any size analysis. Cite it as methodology kin (evidence surfaces,
  explicit unknown/contradiction handling, "endpoint capability exceeds what
  any single classical session view reveals"); it competes with nothing here.
- **Red Sift** published the exact analytical framing
  (redsift.com/blog/post-quantum-signature-sizes: "ML-DSA certificate chains blow
  past the 14.5 KB TCP congestion window"), employs Ivan Ristić, and already
  ships per-domain certificate products. The distance from their blog to this
  feature is one sprint. This affects schedule, never claim discipline.
- The arXiv metadata search was rate-limited (HTTP 429) during the sweep, so
  coverage of unpublished or blog-only work is not exhaustive. Re-sweep before
  publication.

## The hostile-reviewer arguments, recorded so the writeup answers them

1. **"The claim is gerrymandered."** Every component is published; the
   contribution is a composition of two published methods. Answer: frame it as
   the join, cite both halves prominently, and never use "no published work
   provides" language.
2. **"The projection is arithmetically trivial: the classical distribution
   shifted by a constant."** The ML-DSA delta per certificate follows from FIPS
   204, so a reviewer will say the result is (depth x ~3.7KB) + (SCT count x
   ~2.4KB) applied to published depth distributions. Answer: make this the
   research question. Measure whether per-site variance in extension bloat, SAN
   count and SCT count moves the projected tail materially away from the
   constant-delta model. If yes, that is the finding. If no, say so plainly and
   ship the dataset and tool without a distributional claim.
3. **"Per-site is really CDN-weighted."** Published concentration figures:
   ~70% of PQ-TLS deployment attributable to two providers (Mind the Gap),
   Cloudflare at 37.97% of scanned domains (Dubey). Answer: the unit of analysis
   is distinct chain shapes with population weights, stated up front.
4. **"The projection is assumption-dominated."** Parameter set, intermediate
   migration, SCT migration, and whether the root is on the wire each move the
   answer by more than per-site variance might. Answer: scenarios, not a single
   number, with every assumption named, and every projected figure stamped
   Proposed.

## Fabrication log

Search summaries fabricated or misattributed twice during this sweep alone,
consistent with this project family's history (three prior demotions in
`pqc-cert-matrix`):

1. A summary attributed "3,309 bytes of CertificateVerify" to arXiv:2604.06100;
   the figure is not in the paper (caught in the earlier cert-matrix sweep,
   recorded here because the same source is cited).
2. A summary attributed ePrint 2022/1556 to "Kampanakis and Kallitsis"; the
   actual authors are Sikeridis, Huntley, Ott and Devetsikiotis.
3. 2026-08-09, compression sweep. A search summary asserted that post-quantum
   certificate overhead "is largely mitigated through TLS 1.3 certificate
   compression and caching mechanisms," and offered arXiv:2604.06100 among its
   sources. That paper contains one instance of the word "compress" and it is
   metaphorical ("compresses the operational meaning"). The assertion also
   contradicts both IETF drafts on the subject. It traces to no source that
   could be opened.

Rule, unchanged: every load-bearing citation is verified by downloading the full
text and grepping it. Never a summary.

## Pre-publication re-sweep, 2026-08-07 (same night as the article)

arXiv API returned 200 on every query this time, closing the earlier 429 gap: 37
cs.CR post-quantum submissions since 2026-06-10 reviewed. The join claim stays
clear. Three corrections were forced into the article before it shipped:

- **"The models conclude ML-DSA-44 fits" was refutable.** Kampanakis and
  Kallitsis's own text (local copy, `.sources/priorart/`): "When SCTs and/or
  OCSP staples are present Dilithium starts from ~15KB." And Ristic (Red Sift,
  2026-08-03, redsift.com/blog/post-quantum-signature-sizes) concludes on a
  modeled chain that "the public cryptography alone busts the 14 KB initial
  congestion window", and closes by announcing a measured follow-up post. The
  honest framing: models disagree by chain flavor; the corpus supplies the
  fraction and the spread.
- **The Sikeridis depth comparison needs its counting rule.** Our 3-ICA bucket
  matches their June 2022 row within a point while 0-ICA sits 24 points apart
  (0.6% vs 24.1%); some of the table is definitional, and Sikeridis never
  state their rule. Stated in the article.
- **The HRR observation is a conformance check, not a finding.** RFC 8446
  section 4.1.4 specifies it; Cloudflare documented the dual-key-share
  mitigation in 2023 (blog.cloudflare.com/post-quantum-to-origins/);
  draft-ietf-tls-key-share-prediction exists to avoid it via DNS. No published
  measurement of a PQ-only-key-share client against classical servers was
  found, so the 284/285 number itself is ours.

New sources recorded: Yao et al., "Chaos in the Chain", ACM IMC 2025 (DOI
10.1145/3730567.3732921), Tranco 1M chain completeness, zero PQ/size content;
its 89.9% root-omitted and 1.3% no-intermediate cross-check this corpus's 86.9%
and 0.6%. Loizou and Ghadafi (arXiv:2608.02147, UK sectors, adoption only): not
preempting. Kim et al. (arXiv:2607.20800) and Lee et al. (ePrint 2026/1416):
verifier semantics, not preempting; 1416's abstract independently states the
wolfSSL cannot-require finding, cite it wherever the catalyst line appears.

**Still unopened:** Henrich, Schmitt, Alnahawi, Heinemann, ISC 2025 (LNCS
16186, DOI 10.1007/978-3-032-08124-7_6), paywalled, varies lab chain
compositions; article wording was chosen so nothing depends on it. ePrint
2026/1416 PDF still 403s; abstract only.
