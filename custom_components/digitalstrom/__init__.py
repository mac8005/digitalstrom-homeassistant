"""The digitalSTROM integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_TOKEN,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.event import async_track_time_interval

from .api.apartment import DigitalstromApartment
from .api.client import DigitalstromClient
from .api.exceptions import CannotConnect, InvalidAuth, InvalidCertificate, ServerError
from .const import CONF_DSUID, CONF_SSL, DOMAIN, WEBSOCKET_WATCHDOG_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.UPDATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.SCENE,
    Platform.CLIMATE,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    """
    load configuration for digitalSTROM component
    """
    # not configured
    if DOMAIN not in config:
        return True

    # already imported
    if hass.config_entries.async_entries(DOMAIN):
        return True

    return True


async def async_refresh_device_availability(hass, entry, apartment) -> None:
    """Reconcile cached availability with the server's device inventory."""
    data = await apartment.client.request("apartment/getDevices")
    changed = set()
    for item in data:
        dsuid = item.get("dSUID")
        present = item.get("isPresent")
        device = apartment.devices.get(dsuid)
        if device is not None and type(present) is bool and device.available != present:
            device.availability_callback(present)
            changed.add(dsuid)

    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.disabled_by is not None:
            continue
        dsuid = entity.unique_id.split("_", 1)[0]
        device = apartment.devices.get(dsuid)
        state = hass.states.get(entity.entity_id)
        if device is None or state is None:
            continue
        if dsuid in changed or (state.state != "unavailable") != device.available:
            await async_update_entity(hass, entity.entity_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up digitalSTROM from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    client = DigitalstromClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        ssl=entry.data[CONF_SSL],
        loop=hass.loop,
    )
    client.set_app_token(entry.data[CONF_TOKEN])

    try:
        apartment = DigitalstromApartment(client, entry.data[CONF_DSUID])
        hass.data[DOMAIN].setdefault(entry.data[CONF_DSUID], dict())
        hass.data[DOMAIN][entry.data[CONF_DSUID]]["client"] = client
        hass.data[DOMAIN][entry.data[CONF_DSUID]]["apartment"] = apartment
        await apartment.get_zones()
        await apartment.get_circuits()
        await apartment.get_devices()
    except (InvalidAuth, InvalidCertificate) as ex:
        raise ConfigEntryAuthFailed(ex) from ex
    except (CannotConnect, ServerError) as ex:
        raise ConfigEntryNotReady(ex) from ex

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    availability_lock = asyncio.Lock()

    async def refresh_availability(now):
        if availability_lock.locked():
            return
        async with availability_lock:
            try:
                async with asyncio.timeout(30):
                    await async_refresh_device_availability(hass, entry, apartment)
            except (
                CannotConnect, InvalidAuth, InvalidCertificate, ServerError,
                HomeAssistantError, TimeoutError,
            ) as err:
                _LOGGER.warning("Could not refresh digitalSTROM availability: %s", err)

    entry.async_on_unload(
        async_track_time_interval(hass, refresh_availability, timedelta(minutes=1))
    )

    async def start_watchdog(event=None):
        """Start websocket watchdog."""
        if "watchdog" not in hass.data[DOMAIN][entry.data[CONF_DSUID]]:
            hass.data[DOMAIN][entry.data[CONF_DSUID]]["watchdog"] = (
                async_track_time_interval(
                    hass,
                    client.event_listener_watchdog,
                    WEBSOCKET_WATCHDOG_INTERVAL,
                    cancel_on_shutdown=True,
                )
            )

    async def stop_watchdog(event=None):
        await async_unload_entry(hass, entry)

    # If Home Assistant is already in a running state, start the watchdog
    # immediately, else trigger it after Home Assistant has finished starting.
    if hass.state == CoreState.running:
        await start_watchdog()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_watchdog)
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, client.event_listener_watchdog
        )
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_watchdog)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if entry.data[CONF_DSUID] in hass.data[DOMAIN] and (
            (remove_watchdog := hass.data[DOMAIN][entry.data[CONF_DSUID]]["watchdog"])
            is not None
        ):
            remove_watchdog()
        await hass.data[DOMAIN][entry.data[CONF_DSUID]]["client"].stop_event_listener()
        hass.data[DOMAIN].pop(entry.data[CONF_DSUID])
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: AugustConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove config entry from a device if it's no longer present."""
    return True
