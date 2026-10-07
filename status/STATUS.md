# Status
Updated: 2026-10-07

## In flight
- Port verified availability reconciliation and parent callback repair into this maintained fork; preserve the existing scene API compatibility fix. HACS migration pending.

## Decisions
- Preserve the digitalstrom integration domain and entity identifiers to retain existing HA configuration.
- Keep household configuration, identifiers and credentials outside this repository.

## Next
1. Port the deployed fixes, run focused regression checks and publish a versioned release.
2. Point HACS at this fork and verify the installed files and integration health.

## Gotchas
- Upstream v0.0.13 can retain stale device availability after dSS rediscovery.

## Log
- 2026-10-07: Created maintained fork for verified availability and scene compatibility fixes.
