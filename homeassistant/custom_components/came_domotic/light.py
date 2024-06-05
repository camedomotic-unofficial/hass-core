"""Platform for light integration."""

from __future__ import annotations

from typing import Any

import came_domotic_unofficial.models as camelib_models

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CAME_BASIC_FORM_SCHEMA, LOGGER, utils_normalize_string
from .coordinator import CameDataUpdateCoordinator
from .entity import CameDomoticEntity

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(CAME_BASIC_FORM_SCHEMA)


def create_light_entity_descriptor(light_id: str, name: str) -> LightEntityDescription:
    """Create a light entity description."""
    return LightEntityDescription(
        key=f"light_{light_id}_{utils_normalize_string(name)}",
        has_entity_name=True,
        name=name,
    )


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
    came_lights = await coordinator.client.async_get_lights()
    async_add_entities(CameLight(coordinator, light) for light in came_lights)


class CameLight(CameDomoticEntity, LightEntity):
    """Representation of CAME Domotic light device."""

    def __init__(
        self,
        coordinator: CameDataUpdateCoordinator,
        light: camelib_models.CameLight,
    ) -> None:
        """Initialize an CameLight."""
        # LOGGER.debug("[CameLight] __init__. Light name: %s", light.name)
        super().__init__(coordinator)
        self.coordinator: CameDataUpdateCoordinator = coordinator
        self.entity_description = create_light_entity_descriptor(
            light.act_id, light.name
        )
        self._api_light: camelib_models.CameLight = light
        self._name: str = light.name

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name or ""

    @property
    def brightness(self) -> int:
        """Return the brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._util_255_to_100(self._api_light.perc) or 100

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._api_light.status is camelib_models.LightStatus.ON

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the light."""
        return (
            ColorMode.BRIGHTNESS
            if self._api_light.type == camelib_models.LightType.DIMMER
            else ColorMode.ONOFF
        )

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes."""
        return {
            ColorMode.BRIGHTNESS
            if self._api_light.type == camelib_models.LightType.DIMMER
            else ColorMode.ONOFF
        }

    @property
    def came_id(self) -> int:
        """CAME Domotic ID of the light."""
        result: int = self._api_light.act_id
        return result

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        LOGGER.debug(
            "[CameLight] async_turn_on. Light name: %s, brightness: %s",
            self._name,
            kwargs.get(ATTR_BRIGHTNESS, 100),
        )
        await self._api_light.async_set_status(
            camelib_models.LightStatus.ON,
            self._util_255_to_100(kwargs.get(ATTR_BRIGHTNESS, 100)),
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        await self._api_light.async_set_status(camelib_models.LightStatus.OFF)

    async def async_set_brightness(self, brightness: int) -> None:
        """Set the brightness of the light."""

        LOGGER.debug(
            "[CameLight] async_set_brightness. Light name: %s, brightness: %s",
            self._name,
            brightness,
        )

        await self._api_light.async_set_status(
            self._api_light.status, self._util_255_to_100(brightness)
        )

    async def async_update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """

        await self.coordinator.async_refresh()
        lights = self.coordinator.data.lights

        # Set self._light to the item in lights that has the same act_id as self._light
        light: CameLight = (
            next(light for light in lights if light.act_id == self.came_id)
            if lights
            else None
        )

        if not light:
            LOGGER.warning("Light with ID %s not found anymore", self.came_id)
            return
        self._api_light = light

    @staticmethod
    def _util_100_to_255(value: int) -> int:
        """Convert a value from 0-100 to 0-255."""
        return max(0, min(255, int(value * 255 / 100)))

    @staticmethod
    def _util_255_to_100(value: int) -> int:
        """Convert a value from 0-255 to 0-100."""
        return max(0, min(100, int(value * 100 / 255)))
