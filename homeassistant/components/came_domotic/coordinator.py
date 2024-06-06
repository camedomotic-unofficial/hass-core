"""DataUpdateCoordinator for came_domotic."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import came_domotic_unofficial as camelib
import came_domotic_unofficial.errors as camelib_errors
import came_domotic_unofficial.models as camelib_models

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE, CONF_LIGHTS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, FEATURE_LIGHTS, LOGGER


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CameDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: camelib.CameDomoticAPI,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.client = client
        self.data: CameCoordinatorData = CameCoordinatorData()

    async def _async_update_data(self) -> CameCoordinatorData:
        """Update data via library."""
        try:
            api = self.client

            # Initialize the server information and features
            # No need to update since they're a static server configuration
            self.data[CONF_DEVICE] = self.data[
                CONF_DEVICE
            ] or CameCoordinatorServerInfo(await api.async_get_server_info())

            server_info: CameCoordinatorServerInfo | None = self.data.get(CONF_DEVICE)

            # Check whether the feature "lights" is enabled
            if server_info and FEATURE_LIGHTS in server_info.features:
                await self._async_update_lights(api)

            return self.data  # noqa: TRY300
        except camelib_errors.CameDomoticServerNotFoundError as e:
            LOGGER.warning("Server not found!")
            raise ConfigEntryAuthFailed(e) from e
        except camelib_errors.CameDomoticAuthError as e:
            LOGGER.warning("Invalid credentials error: %s", e)
            raise ConfigEntryAuthFailed(e) from e
        except camelib_errors.CameDomoticServerError as e:
            LOGGER.debug(
                "An error occurred while communicating with the server (%s)", e
            )
            raise UpdateFailed(e) from e
        except Exception as e:
            LOGGER.exception("Unexpected error")
            raise UpdateFailed(e) from e

    async def _async_update_lights(self, api: camelib.CameDomoticAPI) -> None:
        """Update lights data."""

        if self.data.get(CONF_LIGHTS):
            updates_counter: int = 0
            updates: camelib_models.CameUpdates = await api.async_get_updates()
            lights: list[camelib_models.CameLight] | None = self.data.get(CONF_LIGHTS)
            # For each item in the updates.light_updates dictionary, update the
            # _api_light.raw_data attribute of the corresponding self.data.lights
            # item, matching on the dictionary key int being equal to the
            # item.came_id value.
            if updates.light_updates and lights:
                for light_id, light_update in updates.light_updates.items():
                    for light in lights:
                        if light.came_id == light_id:
                            light.raw_data = light_update
                            updates_counter += 1
            LOGGER.debug(
                "[_async_update_data] Updated %s light devices",
                updates_counter,
            )
        else:
            # Initialize lights
            self.data[CONF_LIGHTS] = await api.async_get_lights()
            LOGGER.debug(
                "[_async_update_data] Initialized %s light devices",
                len(self.data.get(CONF_LIGHTS, list[Any])),
            )


class CameCoordinatorData(dict[str, Any]):
    """Class to hold coordinator data."""

    def __init__(self) -> None:
        """Initialize."""


class CameEntryRuntimeData:
    """Class to hold the config entry runtime data."""

    def __init__(self) -> None:
        """Initialize."""
        self.coordinator: CameDataUpdateCoordinator


class CameCoordinatorServerInfo:
    """Class to hold server information."""

    def __init__(self, server_info: camelib_models.CameServerInfo) -> None:
        """Initialize."""
        self.keycode: str = server_info.keycode
        self.type: str = server_info.type
        self.serial: str = server_info.serial
        self.swver: str = server_info.swver
        self.board: str = server_info.board
        self.features: list[str] = server_info.features

    def __str__(self) -> str:
        """Return the string representation of the server information."""
        return f"{self.type} (serial: {self.serial}, SW: {self.swver}, HW: {self.board}, features: {self.features})"

    def __repr__(self) -> str:
        """Return the representation of the server information."""
        return f"<CameCoordinatorServerInfo {self.__str__()}>"
