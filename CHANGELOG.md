# Changelog

## 0.0.13.2 — 2026-10-13

- Use platform-correct entity IDs while retaining existing unique IDs and registered entities.
- Resolve parent devices through registry IDs instead of deprecated identifier links.
- Keep digitalSTROM button groups separate from Home Assistant's entity group property.
- Use the supported parts-per-million unit for CO/CO2 sensors.
- Skip redundant climate polling when no supported PID climate zones are configured; preserve retryable configured climate entities on an initial connection failure.
- Check circuit firmware every six hours instead of every fifteen minutes. Manual refresh and installation remain available; light, blind, sensor and availability polling are unchanged.

## 0.0.13.1 — 2026-10-07

- Recover availability from authoritative device presence and preserve parent-device callback handling.
- Retain stable scene identity and avoid inactive production-archive queries for consumption-only meters.
