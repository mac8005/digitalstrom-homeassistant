# Status
Updated: 2026-10-07

## In flight
- Release 0.0.13.1 prepared on maintained-v0.0.13; 15 focused regression cases pass. HACS migration and live metering validation pending.

## Decisions
- Preserve the digitalstrom integration domain and entity identifiers to retain existing HA configuration.
- Keep household configuration, identifiers and credentials outside this repository.

## Next
1. Publish the verified 0.0.13.1 release.
2. Point HACS at this fork and verify the installed files and integration health.

## Gotchas
- Upstream v0.0.13 can retain stale device availability after dSS rediscovery.

## Log
- 2026-10-07: Ported three existing fixes onto stable v0.0.13 and avoided inactive production archive queries for consumption-only meters. Nine availability and six metering regressions pass.
- 2026-10-07: Created maintained fork for verified availability and scene compatibility fixes.
