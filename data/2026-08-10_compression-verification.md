# Verifying the CompressedCertificate count, 2026-08-10

The 3-of-1,019 figure in `2026-08-07_group-subsample.md` came from a best-effort
regex that had never been spot-checked, and the detector is the whole result. So
it was audited before the number went anywhere public.

**Verdict: the count is correct.** The denominator moved, the framing around it
changed, and a hypothesis in `pqc-cert-matrix` turned out to be wrong.

## What the old detector did

```python
compressed_cert=bool(re.search(r"compressed.?certificate", text, re.I))
```

Case-insensitive, unanchored, over stdout and stderr together. The obvious risk
is that every ClientHello advertises `compress_certificate(27)`, so a pattern
that reached it would have flagged all 1,019 hosts. It does not reach it: the
extension name has no "ed", so `compressed.?` cannot bridge to its "certificate".
Confirmed against six live hosts, all six carrying the offer:

| host | pattern matched | `CompressedCertificate` | `compress_certificate` ext |
|---|---|---|---|
| fbsbx.com | 1 | 1 | 1 |
| threads.net | 1 | 1 | 1 |
| messenger.com | 1 | 1 | 1 |
| cloudflare.com | 0 | 0 | 1 |
| google.com | 0 | 0 | 1 |
| example.com | 0 | 0 | 1 |

The detector is now anchored to the start of a trace line anyway
(`COMPCERT_RE` in `src/probe_groups.py`), pinned by
`src/probe_groups_selfcheck.py`. Nothing about the count changes; the old
pattern happened to be safe, and a future trace format change would not be.

## The three hits are real

Genuine RFC 8879 messages on a **Received** record, not client-side artifacts.
fbsbx.com, verbatim:

```
Received TLS Record
  Inner Content Type = Handshake (22)
    CompressedCertificate, Length=2227
      Compression type=zstd (0x0003)
      Uncompressed length=3009
      Compressed length=2219, Ratio=1.356016:1
```

All three reproduced on 2026-08-10, three days after the 2026-08-07 capture, all
three zstd. Counts re-derived from `group-subsample.jsonl`: 1,019 records, 1,019
ok, 3 flagged, 842 TLS 1.3, 177 TLS 1.2, and zero flagged among the TLS 1.2 set,
which is what RFC 8879 requires.

## What changed

**The denominator.** Report 3 of 842 TLS 1.3 sessions (0.36%), not 3 of 1,019. A
TLS 1.2 server could not have compressed under any client.

**The prevalence framing.** All three hits are Meta properties, and every
Meta-family host in the subsample flagged, so the result is internally
consistent. But stride-8 skipped `facebook.com`, `instagram.com`,
`whatsapp.com`, and `fbcdn.net`, and all four also return zstd
CompressedCertificate when probed directly. The subsample undercounts. Cite 3 of
842 as a property of this subsample, never as a rate for the web.

**A `pqc-cert-matrix` hypothesis, now retracted.** That repo recorded a uniform
lab zero and guessed the cause was client-side: that this Ubuntu build sends
OpenSSL's documented default preference order, which leads with a brotli it was
not built with, so negotiation fails instead of falling through. Measured, the
ClientHello carries no such order, only what the build has:

```
extension_type=compress_certificate(27), length=5
  zlib (1)
  zstd (3)
```

And negotiation plainly succeeds when the peer supports it. The lab zero was a
property of the lab servers. Corrected in `pqc-cert-matrix/phase3/FINDINGS.md`
and its `PRIOR-ART.md` the same day.

## Caveat that survives

Compression detection stays client-relative. The offer is zlib and zstd, never
brotli, so a brotli-only server reads as a non-engagement from this build. That
is a real false-negative channel and it is not quantified here.

## Reproduce

```bash
for h in fbsbx.com threads.net messenger.com cloudflare.com google.com; do
  openssl s_client -connect $h:443 -servername $h -trace </dev/null 2>&1 \
    | grep -E '^\s*(CompressedCertificate|Compression type=)' \
    | sed "s|^|$h |"
done

python3 src/probe_groups_selfcheck.py
```

All figures Verified: measured on this machine with OpenSSL 3.5.5 (27 Jan 2026),
output above.
