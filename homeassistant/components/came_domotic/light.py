"""Platform for light integration."""

from __future__ import annotations

from homeassistant.components.light import PLATFORM_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LIGHTS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CAME_BASIC_FORM_SCHEMA
from .coordinator import CameDataUpdateCoordinator
from .entity import CameLight

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(CAME_BASIC_FORM_SCHEMA)


async def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the CAME Domotic platform."""


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the CAME Domotic platform."""
    coordinator: CameDataUpdateCoordinator = config.runtime_data.coordinator
    api_lights = await coordinator.client.async_get_lights()
    async_add_entities(CameLight(coordinator, api_light) for api_light in api_lights)
    coordinator.data[CONF_LIGHTS] = {
        api_light.act_id: api_light for api_light in api_lights
    }
