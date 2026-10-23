# Woon IoT comparison — 2026-10-23

## Recommendation
Keep maintained v0.0.13.3 for now. Woon IoT v4.2.5 is a separate integration, not an upstream update to this fork. Consider a controlled migration evaluation only if zone controls and lower bus load outweigh the loss of device-level functionality.

## Evidence
- Current repository manifest is 0.0.13.3, source release 1d5a294. The October 13 deployment receipt records 28 matching files, 397 preserved registered entities/device links, 181 enabled entities available and 23 passing regressions.
- Live HA SSH authentication was denied from both the local Mac and MacMini. These deployment figures are historical, not verified current runtime state.
- Woon IoT stable v4.2.5 was published October 23. Its release reports faster startup, reduced bus traffic, ventilation and Joker state fixes. The reported traffic reduction compares its own releases, not this fork.
- Domains differ: digitalstrom versus digitalstrom_smart. Woon IoT uses zone unique IDs (ds_<server>_<zone>_light/cover); this fork uses device/output identities. Existing dashboards and automations need migration mapping.
- Woon IoT tagged light.py supports zone brightness only. This fork supports individual outputs with colour temperature, HS and XY commands when hardware supports them.
- Woon IoT tagged cover.py supports zone position/open/close/stop, without tilt features. This fork supports individual position and tilt channels.
- Woon IoT uses events plus fallback/cache polling; it is not polling-free. Its coordinator disables recurring per-device power reads but still confirms selected actuator outputs.
- Woon IoT documentation places climate, circuit energy and several advanced functions behind Pro (advertised EUR 29/year or EUR 89 lifetime). Confirm exact feature coverage before migration.
- Our availability, registry, metering and discovery fixes do not transfer automatically to a different implementation. No evidence establishes that changing integration fixes native bus absence.

## Sources
- https://github.com/wooniot/ha-digitalstrom-smart/releases/tag/v4.2.5
- https://github.com/wooniot/ha-digitalstrom-smart/tree/v4.2.5/custom_components/digitalstrom_smart
- https://github.com/wooniot/ha-digitalstrom-smart
- [Existing release verification](2026-10-13-compatibility.md)

No integration/configuration changes, restarts or physical device commands were performed.
