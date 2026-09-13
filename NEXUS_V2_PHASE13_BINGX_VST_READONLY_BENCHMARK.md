# NEXUS V2 Phase 13 — BingX VST Read-Only Certification Benchmark

## Decision

The first network evidence slice is deliberately read-only. It verifies real
BingX simulated-environment authentication, transport, endpoint availability,
and canonical normalization before any controlled DEMO write certification is
considered.

## External reference findings

Current BingX API reference identifies production-simulated VST endpoints as:

- primary `https://open-api-vst.bingx.com`
- fallback `https://open-api-vst.bingx.pro`

The fallback is appropriate only for network/timeout failure, not business/API
errors. Authenticated requests require an API-key header, HMAC-SHA256 signature,
and millisecond timestamp. The signing input is ASCII-key-sorted and unencoded.
A `recvWindow` no greater than 5000 ms is supported.

Relevant perpetual read endpoints include current positions, account balance,
open orders, single/order history reads, and fill history. Existing NEXUS V2
BingXVenueAdapter owns raw-to-canonical normalization; this slice adds only the
credential-safe transport and real VST read evidence runner.

## NEXUS safety decision

- No REAL base URL in the VST transport.
- Transport rejects every non-GET request before network access.
- Secrets come only from local environment variables.
- Evidence contains no secrets, signatures, raw responses, order/fill IDs, or
  account identifiers.
- No AIEA, ExecutionCoordinator, SQLAlchemy, or direct Core mutation authority.
- Restricted Live and Full Live remain disabled.

## Certification status

This slice can become DONE / TEST VERIFIED after local static/focused/full test
evidence and Git/Audit recording. The venue gate remains OPEN until an actual
credential-safe VST network run returns successful sanitized evidence.
