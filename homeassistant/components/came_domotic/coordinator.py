"""DataUpdateCoordinator for came_domotic."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import came_domotic_unofficial as camelib
import came_domotic_unofficial.errors as camelib_errors
import came_domotic_unofficial.models as camelib_models

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

# from .api import (
#    CameDomoticApiClient,
#    CameDomoticApiClientAuthenticationError,
#    CameDomoticApiClientError,
# )
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
        self.server_info: CameCoordinatorServerInfo | None = None

    async def _async_update_data(self) -> CameCoordinatorData:
        """Update data via library."""
        try:
            api = self.client
            self.server_info = self.server_info or CameCoordinatorServerInfo(
                await api.async_get_server_info()
            )
            self.data.features = self.data.features or [
                await api.async_get_features() or list[camelib_models.CameFeature]
            ]

            if any(feature.name == FEATURE_LIGHTS for feature in self.data.features):
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
        if self.data.lights:
            updates: camelib_models.CameUpdates = await api.async_get_updates()
            # For each item in the updates.light_updates dictionary, update the
            # _api_light.raw_data attribute of the corresponding self.data.lights
            # item, matching on the dictionary key int being equal to the
            # item.came_id value.
            if updates.light_updates:
                for light_id, light_update in updates.light_updates.items():
                    for light in self.data.lights:
                        if light.came_id == light_id:
                            light.raw_data = light_update
            return
        # Initialize lights
        self.data.lights = await api.async_get_lights()
        LOGGER.debug(
            "[_async_update_data] Initialized %s light devices",
            len(self.data.lights) if self.data.lights else 0,
        )


class CameCoordinatorData(dict[str, Any]):
    """Class to hold coordinator data."""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()
        self.features: list[camelib_models.CameFeature] | None = None
        self.lights: list[camelib_models.CameLight] | None = None


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

    def __str__(self) -> str:
        """Return the string representation of the server information."""
        return (
            f"{self.type} (serial: {self.serial}, SW: {self.swver}, HW: {self.board})"
        )

    def __repr__(self) -> str:
        """Return the representation of the server information."""
        return f"<CameCoordinatorServerInfo {self.__str__()}>"
