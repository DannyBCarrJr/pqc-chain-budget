#!/usr/bin/env python3
"""Self-check for the CompressedCertificate detector in probe_groups.py.

The whole 3-of-842 result rests on one regex telling a received handshake
message apart from the client's own advertised extension. Those two strings
differ by three letters, so this pins both against real trace text.

Fixtures are verbatim from `openssl s_client -trace` runs on 2026-08-10:
fbsbx.com (compresses, zstd) and cloudflare.com (does not). Run it directly:

    python3 src/probe_groups_selfcheck.py
"""
from __future__ import annotations

from probe_groups import COMPALG_RE, COMPCERT_RE

# Real received message, fbsbx.com.
POSITIVE = """\
Received TLS Record
Header:
  Version = TLS 1.2 (0x303)
  Content Type = ApplicationData (23)
  Inner Content Type = Handshake (22)
    CompressedCertificate, Length=2227
      Compression type=zstd (0x0003)
      Uncompressed length=3009
      Compressed length=2219, Ratio=1.356016:1
"""

# Real ClientHello offer, present in EVERY capture including servers that
# never compress. This is the string the old `compressed.?certificate`
# pattern had to avoid, and the reason the detector is anchored to ^.
NEGATIVE = """\
Sent TLS Record
    ClientHello, Length=1885
        extension_type=compress_certificate(27), length=5
          zlib (1)
          zstd (3)
"""


def main() -> int:
    assert COMPCERT_RE.search(POSITIVE), "missed a real CompressedCertificate"
    assert COMPALG_RE.search(POSITIVE).group(1) == "zstd", "wrong algorithm parsed"

    assert not COMPCERT_RE.search(NEGATIVE), "matched the client's own offer"
    assert not COMPALG_RE.search(NEGATIVE), "parsed an algorithm from an offer"

    # The extension name must not be reachable even without line anchoring,
    # because "compress_certificate" carries no "ed". If this ever fails, the
    # old pattern was silently counting every host on the internet.
    assert "compressed" not in NEGATIVE.lower(), "extension name gained an 'ed'"

    print("probe_groups detector self-check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
