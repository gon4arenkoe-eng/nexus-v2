# BingX VST Read-Only Network Certification

## Scope

This Phase 13 slice verifies private BingX simulated-environment reads only.
It MUST NOT submit, cancel, amend, close, or otherwise mutate orders or
positions.

## Safety invariants

- Use BingX VST only: `https://open-api-vst.bingx.com` primary and
  `https://open-api-vst.bingx.pro` network-failure fallback.
- Use an API key with read-only permission.
- Never paste API keys or secret keys into ChatGPT, source files, shell history,
  Audit, logs, screenshots, or evidence artifacts.
- Prefer an IP allowlist on the key.
- The certification runner rejects all non-GET transport methods.
- No REAL BingX base URL is present in the VST transport.
- Empty open-order, position, or fill results are valid successful observations.

## Local credential setup

Set secrets only in the local process environment before execution:

```powershell
$env:BINGX_VST_API_KEY = "<set locally>"
$env:BINGX_VST_SECRET_KEY = "<set locally>"
$env:BINGX_VST_SYMBOL = "BTCUSDT"
```

Do not send their values back in chat.

## Certification command

```powershell
py -3.13 .\scripts\certify_bingx_vst_readonly.py
```

Expected evidence is a sanitized JSON object containing only query status,
asset names, counts, symbol, timestamps, and safety booleans. It contains no
credential values, signatures, raw API payloads, order IDs, fill IDs, or
account identifiers.

## Required PASS conditions

- `environment == BINGX_VST`
- `account_query == PASS`
- `open_orders_query == PASS`
- `positions_query == PASS`
- `fills_query == PASS`
- `writes_attempted == false`
- `real_environment_used == false`

A query that returns zero rows is still PASS if the authenticated endpoint and
canonical normalization complete successfully.

## Failure handling

Any authentication, signature, network, schema, unknown payload, or canonical
normalization failure means certification remains OPEN. Do not retry by
switching to the production/live base URL. Do not enable write permission to
work around a read failure.
