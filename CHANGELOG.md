# Changelog

## 0.0.13.1 — 2026-10-07

- Recover device availability after dSS rediscovery even if the ready event was missed; reconcile authoritative presence once per minute.
- Preserve unavailable status for devices that dSS still reports absent.
- Fix parent availability propagation and the scene entity domain.
- Read consumption-only meters through the metering endpoint to avoid querying disabled production archives; retain the existing path when production metering is enabled. Missing readings remain unknown.
- Preserve the v0.0.13 configuration and entity identifiers.

Validation: nine isolated availability and six metering regression cases, deployed HA import/config checks and live presence comparison. This release does not repair electrical communication problems.
