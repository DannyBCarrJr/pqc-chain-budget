#!/usr/bin/env python3
"""Derive per-certificate facts from a raw capture (capture_chains.py output).

Reads raw JSONL, writes summary JSONL. Pure derivation, no network: run it as
many times as needed against the same captured evidence.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.x509.oid import ExtensionOID, NameOID, AuthorityInformationAccessOID
from cryptography.hazmat.primitives.asymmetric import ec, ed448, ed25519, rsa


def ext_value(cert: x509.Certificate, oid: x509.ObjectIdentifier) -> Any | None:
    try:
        return cert.extensions.get_extension_for_oid(oid).value
    except x509.ExtensionNotFound:
        return None


def common_name(name: x509.Name) -> str | None:
    attrs = name.get_attributes_for_oid(NameOID.COMMON_NAME)
    value = attrs[0].value if attrs else None
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else value


def public_key_facts(cert: x509.Certificate) -> tuple[str, int | None]:
    pk = cert.public_key()
    if isinstance(pk, rsa.RSAPublicKey):
        return "RSA", pk.key_size
    if isinstance(pk, ec.EllipticCurvePublicKey):
        return f"EC-{pk.curve.name}", pk.key_size
    if isinstance(pk, ed25519.Ed25519PublicKey):
        return "Ed25519", 256
    if isinstance(pk, ed448.Ed448PublicKey):
        return "Ed448", 456
    return type(pk).__name__, None


def cert_facts(der: bytes) -> dict[str, Any]:
    cert = x509.load_der_x509_certificate(der)
    sig_oid = cert.signature_algorithm_oid
    san = ext_value(cert, ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    scts = ext_value(cert, ExtensionOID.PRECERT_SIGNED_CERTIFICATE_TIMESTAMPS)
    bc = ext_value(cert, ExtensionOID.BASIC_CONSTRAINTS)
    aia = ext_value(cert, ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
    crldp = ext_value(cert, ExtensionOID.CRL_DISTRIBUTION_POINTS)
    ocsp_urls = (
        sum(1 for d in aia if d.access_method == AuthorityInformationAccessOID.OCSP)
        if aia is not None
        else 0
    )
    return {
        "der_len": len(der),
        "sig_alg": getattr(sig_oid, "_name", None) or sig_oid.dotted_string,
        "sig_alg_oid": sig_oid.dotted_string,
        "pubkey_alg": public_key_facts(cert)[0],
        "pubkey_bits": public_key_facts(cert)[1],
        "subject_cn": common_name(cert.subject),
        "issuer_cn": common_name(cert.issuer),
        "self_signed": cert.subject == cert.issuer,
        "is_ca": bool(bc.ca) if bc is not None else False,
        "san_count": len(san) if san is not None else 0,
        "sct_count": len(list(scts)) if scts is not None else 0,
        "ocsp_url_count": ocsp_urls,
        "crl_dp_count": len(crldp) if crldp is not None else 0,
        "ext_count": len(cert.extensions),
    }


def summarize(rec: dict[str, Any]) -> dict[str, Any]:
    out = {k: rec.get(k) for k in ("rank", "domain", "hostname", "ts", "ok", "error", "tls_version", "cipher")}
    if not rec.get("ok"):
        return out
    certs: list[dict[str, Any]] = []
    for b64 in rec.get("certs_der_b64", []):
        der = base64.b64decode(b64)
        try:
            certs.append(cert_facts(der))
        except (ValueError, x509.ExtensionNotFound) as e:
            certs.append({"der_len": len(der), "parse_error": f"{type(e).__name__}: {e}"})
    out.update(
        depth=len(certs),
        total_der_bytes=sum(c["der_len"] for c in certs),
        root_transmitted=bool(certs) and bool(certs[-1].get("self_signed")),
        certs=certs,
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="raw capture JSONL")
    ap.add_argument("--output", required=True, type=Path, help="summary JSONL")
    args = ap.parse_args()

    n_ok = n_fail = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.input.open() as inp, args.output.open("w") as out:
        for line in inp:
            rec = json.loads(line)
            if "_meta" in rec:
                out.write(line)
                continue
            summary = summarize(rec)
            n_ok += 1 if summary.get("ok") else 0
            n_fail += 0 if summary.get("ok") else 1
            out.write(json.dumps(summary) + "\n")
    print(f"parsed: {n_ok} ok, {n_fail} failed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
