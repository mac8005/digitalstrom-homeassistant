# Availability recurrence check — 2026-10-09

Read-only live diagnosis of a light that remained on because a second room actuator was unavailable.

- All 134 matched device entities agree with native digitalSTROM isPresent. No stale HA availability mismatch was reproduced.
- Native inventory has 57 logical device entries; two report absent. All four circuit meters report present and valid. Both absent entries belong to the same circuit.
- All 28 tracked package files match the maintained v0.0.13.1 source. One extra old scene.py backup exists but is not an imported package module.
- Three direct inventory reads succeeded in 143, 300 and 134 ms.
- Integration entry is loaded. Retained logs include intermittent connection failures and climate-platform startup failure, plus future HA deprecation warnings. These do not establish the cause of native device absence or contradict the current availability agreement. Global integration health is not implied by this targeted availability check.
- The room automation blocks its shared off scene when either actuator is unavailable. This is separate from the integration and was not changed by this diagnosis.

No source, runtime configuration, device command, reset, re-registration or reload performed. Native absence needs further bus/supply investigation; do not force availability true based on a cached target output value. Private household names, device identifiers, credentials and detailed runtime evidence remain outside this repository. Prior transmission measurements are historical and were not repeated.
