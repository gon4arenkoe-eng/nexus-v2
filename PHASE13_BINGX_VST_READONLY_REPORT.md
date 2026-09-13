# Phase 13 BingX VST Read-Only Delivery Report

Adds a read-only authenticated BingX VST transport and a sanitized network
certification runner. No order submission/cancellation capability is added.

Expected apply verification:

- authority / REAL-base scan PASS
- Python compile PASS
- flake8 PASS
- mypy PASS
- focused VST transport/cert-runner tests PASS
- existing BingX adapter tests PASS
- generic VenueAdapter contract PASS
- full regression PASS
- Alembic unchanged
- git diff --check PASS

The actual VST network call is intentionally separate from apply verification
because credentials must remain local and must never be embedded in delivery
artifacts or chat messages.
