# Phase 13 — Binance USD-M Runtime Error Evidence v1

Status target: TEST VERIFIED CANDIDATE only. This slice does not certify Binance runtime or enable writes/live trading.

## Purpose

Preserve safe, actionable runtime evidence from Binance USD-M HTTP failures so a 418/429 can be distinguished from credential/signature failures without logging secrets.

## Captured evidence

- HTTP status code;
- Binance JSON `code` and sanitized `msg` when present;
- numeric `Retry-After` seconds when present;
- `X-MBX-USED-WEIGHT-*` and `X-MBX-ORDER-COUNT-*` response headers only.

## Explicitly excluded

- API key;
- secret key;
- request signature;
- Authorization/Cookie headers;
- request URL/query string;
- arbitrary response headers;
- production host or live enablement changes.

## Safety

The existing sandbox host allowlist and default write-disable policy are unchanged. Runtime credential probing remains a separate read-only certification step.
