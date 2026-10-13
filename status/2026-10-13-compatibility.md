# Home Assistant compatibility and polling release — 13 October 2026

Release [v0.0.13.3](https://github.com/mac8005/digitalstrom-homeassistant/releases/tag/v0.0.13.3), source `1d5a294`, is installed through HACS and active after the final controlled Home Assistant restart. The earlier v0.0.13.2 is superseded and its changes are included.

## Changes

- Explicit entity IDs use their platform domain. Existing unique IDs and registered entity IDs/device links are preserved.
- Apartment/circuit registry entries are resolved before platforms are loaded; child metadata uses parent registry IDs rather than the deprecated via_device identifier.
- Button group metadata no longer overrides the Home Assistant entity group attribute.
- CO/CO2 descriptions use UnitOfRatio.PARTS_PER_MILLION.
- Climate setup avoids a redundant query when no supported PID zones exist. Configured climate entities use retryable coordinator refresh and report connection failures through UpdateFailed.
- Firmware checks run every six hours instead of every fifteen minutes, reducing scheduled check cycles by a factor of 24. Manual refresh/installation and live device/availability polling are unchanged. This reduces check frequency; it does not guarantee lower per-request latency.
- Already configured host discovery aborts before a redundant network probe. Disconnected new-server discovery aborts cleanly with translated connection-failure text.

## Verification

All 23 focused regressions pass: nine availability, six metering, five compatibility and three discovery cases. All platform imports were checked against the installed Home Assistant runtime, and six actual entity constructors/parent links were exercised without connected devices.

All 28 installed package files match the release source. The final HA 2026.10.1 instance is RUNNING, the integration is loaded, HACS reports v0.0.13.3 with no restart requirement, and core validation is valid without errors/warnings. All 397 registered entity IDs and device links match the saved pre-update snapshot. All 181 enabled entities are currently available. No previously loaded integration failed to return to loaded; the global HA repair list is empty.

The observed post-restart log contains no repaired compatibility or discovery-job errors. Intermittent direct native-server read failures remain, so available state is not proof of physical switching or reliable network communication. No scene, lamp, blind, lock or heating operation was activated for testing.

## Rollback and limits

An original installed-package archive and registry/config snapshots were taken before installation. Household paths, identifiers, credentials and the detailed verification receipt remain in the private operations repository rather than this source repository. Restore the prior HACS release or saved package and restart HA; preserve later unrelated registry/configuration changes.

Physical network/bus problems are outside this source repair. The live repair pass also records remaining external-provider/device faults in its private report. Repository workflow runs were not available; no GitHub CI pass is claimed.
