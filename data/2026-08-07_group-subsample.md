# Negotiated-group subsample, 2026-08-07

1,019 domains (stride-8 over successful captures), one openssl s_client
-trace connection each, OpenSSL 3.5.5 default client (single
X25519MLKEM768 key share; verified in transcript). Client-relative
figures: they report what servers do when offered THIS client's
defaults. Evidence: data/group-subsample.jsonl.

- Hybrid X25519MLKEM768: 557/1,019 (54.7% of sessions; 66.2% of TLS 1.3).
  Consistent with published adoption (Dubey 49.3% early 2026; Cloudflare
  54% of requests Q2 2026).
- TLS 1.2 still: 177/1,019 (17.4%). Classical TLS 1.3: x25519 219,
  P-256 49, P-384 16.
- HelloRetryRequest: 284/285 classical TLS 1.3 sessions (99.6%). With a
  PQ-first single-key-share client, essentially every classical TLS 1.3
  server costs one extra round trip. Client-policy-dependent; browsers
  sending dual shares avoid this.
- CompressedCertificate engaged at 3 servers: the only live engagement we
  have observed from this client build (pqc-cert-matrix logged zero in lab).

Instrument note: run 1 (-msg) undercounted by bucketing HRR sessions as
unknown (the 'Negotiated TLS1.3 group' line never prints after HRR);
run 2's trace fallback mislabeled 177 TLS 1.2 sessions as hybrid by
echoing the client's own key share. Both artifacts caught by three-run
cross-validation and the protocol/HRR/group cross-tab; the parser now
gates the fallback on TLS 1.3 and detects HRR by the 2-byte key_share
fingerprint. Final figures derive from group_line (authoritative) plus
TLS 1.3-gated trace fallback.
