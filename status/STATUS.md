# Status
Updated: 2026-10-23

## In flight
- No pending software deployment. v0.0.13.3 is installed through HACS and verified after restart; physical operation and intermittent native connectivity remain separate acceptance checks. [Release verification](2026-10-13-compatibility.md).

## Decisions
- Keep v0.0.13.3 after reviewing separate Woon IoT v4.2.5: zone identities, missing light colour/blind tilt controls and Pro gating make this a migration, not an update. [Comparison](2026-10-23-wooniot-comparison.md).
- Release v0.0.13.1 is based on stable upstream v0.0.13, with availability recovery, parent callback, scene identity and consumption-only metering fixes.
- HACS installs v0.0.13.3; all 28 files match source, 397 registered entity IDs/device links preserved, 181 enabled entities currently available. Twenty-three regressions, native imports/constructors and core validation pass.
- Preserve the digitalstrom integration domain and entity identifiers to retain existing HA configuration.
- Keep household configuration, identifiers and credentials outside this repository.

## Next
1. Investigate native bus absence separately from HA state; latest live comparison has zero availability mismatches. See [diagnosis](2026-10-09-availability-check.md).
2. Observe normal household operation and retain focused regression coverage for future updates.
3. Review later upstream changes before rebasing the maintained branch.

## Gotchas
- Software availability recovery does not repair devices genuinely absent from the digitalSTROM bus.
- Release v0.0.13.3 is pinned to source 1d5a294; subsequent status-only commits do not change it.

## Log
- 2026-10-23: Compared Woon IoT v4.2.5 source/release with maintained fork; recommend retaining current version. Live HA SSH authentication denied; no runtime verification or deployment performed.
- 2026-10-13: Published/installed v0.0.13.3 and verified RUNNING/loaded, all package hashes, unchanged 397 registry links, 181 available enabled entities, zero compatibility/discovery errors and valid core config; global repair list empty.
- 2026-10-13: Verified v0.0.13.2 deployment and unchanged registry identities; final startup trace exposed duplicate-discovery disconnect. Prepared v0.0.13.3 with three new passing discovery regressions; deployment pending.
- 2026-10-13: Prepared HA compatibility fixes for entity domains, parent registry IDs, button group and ppm units; removed redundant climate polling and bounded firmware polling to six hours. Twenty regressions and native imports pass; deployment pending.
- 2026-10-09: Physical switching was confirmed despite native absent status. Do not equate isPresent=false with inability to receive group commands; direct output/presence queries timed out, cause remains unproven.
- 2026-10-09: Authorized native server reboot completed; all circuits ready and native inventory returned to 55/57 present. Existing absence persists. Missing targetValue caches after reboot can yield unknown HA light state despite a valid direct output read; no source change in this task.
- 2026-10-09: Read-only recurrence check: 134 entity availability states match native presence; all 28 package files match v0.0.13.1. Two native device entries absent, all four circuits present. No software change justified.
- 2026-10-07: Published v0.0.13.1, migrated HACS and verified restart, installed package, live counters and availability; no recurring production-archive warnings in the observed post-load window. Fifteen focused regressions pass.
- 2026-10-07: Ported three existing fixes onto stable v0.0.13 and avoided inactive production archive queries for consumption-only meters. Nine availability and six metering regressions pass.
- 2026-10-07: Created maintained fork for verified availability and scene compatibility fixes.
