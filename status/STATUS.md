# Status
Updated: 2026-10-09

## In flight
- No pending software deployment. Real household operation remains the final acceptance check.

## Decisions
- Release v0.0.13.1 is based on stable upstream v0.0.13, with availability recovery, parent callback, scene identity and consumption-only metering fixes.
- HACS now installs this fork; all 28 installed package files matched the release before a successful Home Assistant restart. Integration loaded and authoritative presence reconciliation verified.
- Preserve the digitalstrom integration domain and entity identifiers to retain existing HA configuration.
- Keep household configuration, identifiers and credentials outside this repository.

## Next
1. Investigate native bus absence separately from HA state; latest live comparison has zero availability mismatches. See [diagnosis](2026-10-09-availability-check.md).
2. Observe normal household operation and retain focused regression coverage for future updates.
3. Review later upstream changes before rebasing the maintained branch.

## Gotchas
- Software availability recovery does not repair devices genuinely absent from the digitalSTROM bus.
- Release v0.0.13.1 remains pinned to its tested source commit; subsequent status-only commits do not change it.

## Log
- 2026-10-09: Read-only recurrence check: 134 entity availability states match native presence; all 28 package files match v0.0.13.1. Two native device entries absent, all four circuits present. No software change justified.
- 2026-10-07: Published v0.0.13.1, migrated HACS and verified restart, installed package, live counters and availability; no recurring production-archive warnings in the observed post-load window. Fifteen focused regressions pass.
- 2026-10-07: Ported three existing fixes onto stable v0.0.13 and avoided inactive production archive queries for consumption-only meters. Nine availability and six metering regressions pass.
- 2026-10-07: Created maintained fork for verified availability and scene compatibility fixes.
