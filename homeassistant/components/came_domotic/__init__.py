"""Custom integration to integrate came_domotic with Home Assistant.

For more details about this integration, please refer to
https://github.com/camedomotic-unofficial/came_domotic
"""

from __future__ import annotations

from datetime import timedelta

import aiocamedomotic as camelib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.debounce import Debouncer

from .const import (
    DOMAIN,
    LOGGER,
    REQUEST_REFRESH_DELAY,
    SERVERINFO_BOARD,
    SERVERINFO_FEATURES,
    SERVERINFO_KEYCODE,
    SERVERINFO_SERIAL,
    SERVERINFO_SWVER,
    SERVERINFO_TYPE,
    UPDATE_INTERVAL_SECS,
)
from .coordinator import CameDataUpdateCoordinator, CameEntryRuntimeData

REQUIREMENTS = ["aiohue==1.3.0"]

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
]


# async def async_setup(hass: HomeAssistant, config: ConfigEntry):
#    """Set up the CAME Domotic platform."""
#    # Use `hass.async_create_task` to avoid a circular dependency between the platform and the component
#    #hass.async_create_task(
#    #    hass.config_entries.async_forward_entry_setup(config, "light")
#    #)
#    # Return boolean to indicate that initialization was successful.
#    return True


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an existing CAME Domotic config entry."""
    hass.data.setdefault(DOMAIN, {})

    LOGGER.debug("Setting up entry %s", entry.title)
    coordinator: CameDataUpdateCoordinator = CameDataUpdateCoordinator(
        hass=hass,
        client=await camelib.CameDomoticAPI.async_create(
            entry.data.get(CONF_HOST),
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            websession=aiohttp_client.async_get_clientsession(hass),
        ),
        name=entry.unique_id or DOMAIN,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_SECS),
        request_refresh_debouncer=Debouncer(
            hass, LOGGER, cooldown=REQUEST_REFRESH_DELAY, immediate=False
        ),
    )
    coordinator.data[SERVERINFO_BOARD] = entry.data.get(SERVERINFO_BOARD)
    coordinator.data[SERVERINFO_FEATURES] = entry.data.get(SERVERINFO_FEATURES)
    coordinator.data[SERVERINFO_KEYCODE] = entry.data.get(SERVERINFO_KEYCODE)
    coordinator.data[SERVERINFO_SERIAL] = entry.data.get(SERVERINFO_SERIAL)
    coordinator.data[SERVERINFO_SWVER] = entry.data.get(SERVERINFO_SWVER)
    coordinator.data[SERVERINFO_TYPE] = entry.data.get(SERVERINFO_TYPE)

    entry.runtime_data = CameEntryRuntimeData(coordinator)

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await coordinator.async_config_entry_first_refresh()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of a CAME Domotic config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data: CameEntryRuntimeData = entry.runtime_data
        await data.coordinator.client.async_dispose()
        entry.runtime_data = None
        if len(hass.data[DOMAIN]) == 0:
            hass.data.pop(DOMAIN)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a CAME Domotic config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
