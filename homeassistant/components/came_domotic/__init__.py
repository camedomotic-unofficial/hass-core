"""Custom integration to integrate came_domotic with Home Assistant.

For more details about this integration, please refer to
https://github.com/camedomotic-unofficial/came_domotic
"""

from __future__ import annotations

import came_domotic_unofficial as camelib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, LOGGER
from .coordinator import (
    CameCoordinatorServerInfo,
    CameDataUpdateCoordinator,
    CameEntryRuntimeData,
)

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
    entry.runtime_data = CameEntryRuntimeData()

    # hass.data[DOMAIN][entry.entry_id] = coordinator =
    entry.runtime_data.coordinator = coordinator = CameDataUpdateCoordinator(
        hass=hass,
        client=await camelib.CameDomoticAPI.async_create(
            entry.data.get(CONF_HOST),
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            websession=aiohttp_client.async_get_clientsession(hass),
        ),
    )
    coordinator.data[CONF_DEVICE] = CameCoordinatorServerInfo(
        entry.data.get(CONF_DEVICE)
    )
    LOGGER.debug("Setting up entry %s", entry.title)

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # hass.config_entries.async_update_entry(entry, data=entry.data)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of a CAME Domotic config entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data = None
        if len(hass.data[DOMAIN]) == 0:
            hass.data.pop(DOMAIN)
        # await hass.config_entries.async_remove(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a CAME Domotic config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
