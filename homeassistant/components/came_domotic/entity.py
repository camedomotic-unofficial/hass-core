"""BlueprintEntity class."""

from __future__ import annotations

from typing import Any

import aiocamedomotic.models as camelib_models

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.const import CONF_HOST, CONF_LIGHTS
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    DOMAIN,
    LOGGER,
    MANUFACTURER,
    SERVERINFO_BOARD,
    SERVERINFO_SERIAL,
    SERVERINFO_SWVER,
    SERVERINFO_TYPE,
    create_entity_unique_id,
)
from .coordinator import CameDataUpdateCoordinator


def create_entity_descriptor(id: int, name: str) -> EntityDescription:
    """Create a light entity description."""
    return EntityDescription(
        key=create_entity_unique_id(id, name),
        has_entity_name=True,
        name=name,
    )


class CameDomoticEntity(CoordinatorEntity):
    """CameDomoticEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: CameDataUpdateCoordinator,
        came_entity: camelib_models.base.CameEntity | camelib_models.Light,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        name: str = (
            came_entity.name
            if isinstance(came_entity, camelib_models.Light)
            else coordinator.config_entry.title
        )
        came_id: int = (
            came_entity.act_id if isinstance(came_entity, camelib_models.Light) else 0
        )
        unique_id: str = create_entity_unique_id(came_id, name)
        host: str = coordinator.config_entry.data.get(CONF_HOST, "")

        self._attr_unique_id = unique_id
        if isinstance(came_entity, camelib_models.Light):
            self.entity_id = "light." + unique_id
        self._name: str = name
        self._api_entity: camelib_models.base.CameEntity = came_entity
        self.entity_description = create_entity_descriptor(came_id, name)
        self._attr_device_info = (
            DeviceInfo(
                identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
                name=coordinator.config_entry.title,
                model=f"Server type: {coordinator.data.get(SERVERINFO_TYPE)}",
                manufacturer=MANUFACTURER,
                configuration_url=f"http://{host}/index_setup.html" if host else None,
                serial_number=coordinator.data.get(SERVERINFO_SERIAL),
                sw_version=coordinator.data.get(SERVERINFO_SWVER),
                hw_version=coordinator.data.get(SERVERINFO_BOARD),
            )
            if coordinator.data.get(SERVERINFO_SERIAL)
            else DeviceInfo(
                identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
                name=coordinator.config_entry.title,
                manufacturer=MANUFACTURER,
                configuration_url=f"http://{host}/index_setup.html" if host else None,
            )
        )


class CameLight(CameDomoticEntity, LightEntity):
    """Representation of CAME Domotic light device."""

    _attr_has_entity_name = True
    _attr_name = "camelight"

    def __init__(
        self,
        coordinator: CameDataUpdateCoordinator,
        came_light: camelib_models.Light,
    ) -> None:
        """Initialize an CameLight."""
        # LOGGER.debug("[CameLight] __init__. Light name: %s", light.name)
        super().__init__(coordinator, came_light)
        # self.coordinator = coordinator
        self._attr_is_on = came_light.status is camelib_models.LightStatus.ON
        self._attr_brightness = (
            self._util_100_to_255(came_light.perc) if came_light.perc else 255
        )

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
        return self._attr_brightness or 255

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._api_entity.status is camelib_models.LightStatus.ON

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the light."""
        return (
            ColorMode.BRIGHTNESS
            if self._api_entity.type == camelib_models.LightType.DIMMER
            else ColorMode.ONOFF
        )

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        """Flag supported color modes."""
        return {
            ColorMode.BRIGHTNESS
            if self._api_entity.type == camelib_models.LightType.DIMMER
            else ColorMode.ONOFF
        }

    @property
    def came_id(self) -> int:
        """CAME Domotic ID of the light."""
        result: int = self._api_entity.act_id
        return result

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self.entity_description.key

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        brightness_perc = self._util_255_to_100(kwargs.get(ATTR_BRIGHTNESS))
        LOGGER.debug(
            "[CameLight] async_turn_on. Light name: %s, brightness percentage: %s",
            self._name,
            brightness_perc,
        )
        await self._api_entity.async_set_status(
            camelib_models.LightStatus.ON,
            brightness_perc,
        )
        self._attr_is_on = True
        if brightness_perc:
            self._attr_brightness = self._util_100_to_255(brightness_perc)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        LOGGER.debug(
            "[CameLight] async_turn_off. Light name: %s",
            self._name,
        )
        await self._api_entity.async_set_status(camelib_models.LightStatus.OFF)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_set_brightness(self, **kwargs: Any) -> None:
        """Set the brightness of the light."""

        # If brightness is not provided, return (nothing to do)
        if not kwargs.get(ATTR_BRIGHTNESS):
            return

        brightness_perc = self._util_255_to_100(kwargs.get(ATTR_BRIGHTNESS)) or 255

        LOGGER.debug(
            "[CameLight] async_set_brightness. Light name: %s, brightness percentage: %s",
            self._name,
            brightness_perc,
        )

        if brightness_perc > 0:
            await self._api_entity.async_set_status(
                camelib_models.LightStatus.ON, brightness_perc
            )
            self._attr_is_on = True
            self._attr_brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
            self.async_write_ha_state()
        else:
            await self._api_entity.async_set_status(camelib_models.LightStatus.OFF)
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        # Wait 3 seconds before updating the light
        # await asyncio.sleep(3)

        await self.coordinator.async_refresh()
        lights = self.coordinator.data[CONF_LIGHTS]

        # Set self._light to the item in lights that has the same act_id as self._light
        light: camelib_models.Light = (
            next(light for light in lights if light.act_id == self.came_id)
            if lights
            else None
        )

        if not light:
            LOGGER.warning("Light with ID %s not found anymore", self.came_id)
            return
        self._api_entity = light
        self._attr_is_on = light.status is camelib_models.LightStatus.ON
        self._attr_brightness = self._util_100_to_255(light.perc) if light.perc else 255
        self.async_write_ha_state()

    @staticmethod
    def _util_100_to_255(value: int | None = None) -> int | None:
        """Convert a value from 0-100 to 0-255."""
        if value is None:
            return None
        return max(0, min(255, int(value * 255 / 100)))

    @staticmethod
    def _util_255_to_100(value: int | None = None) -> int | None:
        """Convert a value from 0-255 to 0-100."""
        if value is None:
            return None
        return max(0, min(100, int(value * 100 / 255)))
