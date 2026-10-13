# Changelog

## 0.0.13.3 — 2026-10-13

- Skip duplicate server discovery before making a network probe. Abort disconnected new-server discovery cleanly instead of raising an unhandled job exception.
- Includes all compatibility and polling improvements from 0.0.13.2.

## 0.0.13.2 — 2026-10-13

- Use platform-correct entity IDs while retaining existing unique IDs and registered entities.
- Resolve parent devices through registry IDs instead of deprecated identifier links.
- Keep digitalSTROM button groups separate from Home Assistant's entity group property.
- Use the supported parts-per-million unit for CO/CO2 sensors.
- Skip redundant climate polling when no supported PID climate zones are configured; preserve retryable configured climate entities on an initial connection failure.
- Check circuit firmware every six hours instead of every fifteen minutes. Manual refresh and installation remain available; light, blind, sensor and availability polling are unchanged.

## 0.0.13.1 — 2026-10-07

- Recover device availability after dSS rediscovery even if the ready event was missed; reconcile authoritative presence once per minute.
- Preserve unavailable status for devices that dSS still reports absent.
- Fix parent availability propagation and the scene entity domain.
- Read consumption-only meters through the metering endpoint to avoid querying disabled production archives; retain the existing path when production metering is enabled. Missing readings remain unknown.
- Preserve the v0.0.13 configuration and entity identifiers.

Validation: nine isolated availability and six metering regression cases, deployed HA import/config checks and live presence comparison. This release does not repair electrical communication problems.
