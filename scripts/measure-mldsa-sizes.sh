#!/usr/bin/env bash
# Measure ML-DSA SPKI (DER SubjectPublicKeyInfo) and raw signature sizes with
# the local OpenSSL. These are the Verified constants used by
# src/project_chains.py; rerun after any OpenSSL upgrade and update the
# constants if they move (they should not: FIPS 204 fixes them).
set -euo pipefail
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
cd "$workdir"

openssl version
printf 'test' > msg.bin
for alg in ML-DSA-44 ML-DSA-65 ML-DSA-87; do
  openssl genpkey -algorithm "$alg" -out key.pem 2>/dev/null
  openssl pkey -in key.pem -pubout -outform DER -out spki.der
  openssl pkeyutl -sign -inkey key.pem -rawin -in msg.bin -out sig.bin
  echo "$alg: spki=$(stat -c%s spki.der) sig=$(stat -c%s sig.bin)"
done
