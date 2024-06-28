"""DataUpdateCoordinator for came_domotic."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import aiocamedomotic as camelib
import aiocamedomotic.errors as camelib_errors
import aiocamedomotic.models as camelib_models

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LIGHTS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, UPDATES_CMD_LIGHTS


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CameDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: camelib.CameDomoticAPI,
        *,
        update_interval: timedelta = timedelta(minutes=1),
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client
        self.data: CameCoordinatorData = CameCoordinatorData()

    async def _async_update_data(self) -> CameCoordinatorData:
        """Update data via library."""
        LOGGER.debug("[_async_update_data] Updating data")
        try:
            updates: camelib_models.UpdateList = await self.client.async_get_updates()

            if updates:
                updates_lights: list[dict] = [
                    item
                    for item in updates
                    if item.get("cmd_name") == UPDATES_CMD_LIGHTS
                ]
                if updates_lights:
                    await self._async_update_lights(updates_lights)

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

    async def _async_update_lights(self, light_updates: list[dict]) -> None:
        """Update lights data."""

        initialized: bool = False

        if self.data.get(CONF_LIGHTS):
            lights: dict[int, camelib_models.Light] | None = self.data.get(CONF_LIGHTS)
            if lights is not None:
                initialized = True
                counter: int = 0
                for light_update in light_updates:
                    updated_light_id: int | None = light_update.get("act_id")
                    if updated_light_id is not None:
                        updated_light: camelib_models.Light | None = lights.get(
                            updated_light_id
                        )
                        if updated_light:
                            updated_light = light_update
                            counter += 1
                        else:
                            LOGGER.warning(
                                "Cannot update light with act_id %s: not found in current lights list",
                                updated_light_id,
                            )
                # self.data[CONF_LIGHTS] = lights
                LOGGER.debug(
                    "[_async_update_data] Processed %s light device updates",
                    counter,
                )
        if not initialized:
            # Initialize lights
            init_lights: list[
                camelib_models.Light
            ] = await self.client.async_get_lights()
            # Set self.data[CONF_LIGHTS] as a dictionary with the act_id as the key
            # and the light object as the value

            lights_list: dict[int, camelib_models.Light] = {
                light.act_id: light for light in init_lights
            }
            self.data[CONF_LIGHTS] = lights_list
            LOGGER.debug(
                "[_async_update_data] Initialized %s light devices",
                len(lights_list) if lights_list else 0,
            )


class CameCoordinatorData(dict[str, Any]):
    """Class to hold coordinator data."""

    def __init__(self) -> None:
        """Initialize."""


class CameEntryRuntimeData:
    """Class to hold the config entry runtime data.

    It includes the current instance of the coordinator.
    """

    def __init__(
        self,
        coordinator: CameDataUpdateCoordinator,
    ) -> None:
        """Initialize."""
        self.coordinator: CameDataUpdateCoordinator = coordinator
