"""DataUpdateCoordinator for came_domotic."""

from __future__ import annotations

from collections.abc import Coroutine
from datetime import timedelta
from typing import Any

import aiocamedomotic as camelib
import aiocamedomotic.errors as camelib_errors
import aiocamedomotic.models as camelib_models

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LIGHTS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers.debounce import Debouncer
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
        name: str = DOMAIN,
        update_interval: timedelta | None = None,
        request_refresh_debouncer: Debouncer[Coroutine[Any, Any, None]] | None = None,
        always_update: bool = True,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=name,
            update_method=self.async_update,
            update_interval=update_interval,
            request_refresh_debouncer=request_refresh_debouncer,
            always_update=always_update,
        )
        self.client = client
        self.data: CameCoordinatorData = CameCoordinatorData()

    async def async_update(self) -> CameCoordinatorData:
        """Update data via library."""
        LOGGER.debug("[_async_update_data] Updating data")
        try:
            # Initialize entities if not already done
            if self.data.get(CONF_LIGHTS) is None:
                await self.async_update_lights()

            updates: camelib_models.UpdateList = await self.client.async_get_updates()

            if updates:
                updates_lights: list[dict] = [
                    item
                    for item in updates
                    if item.get("cmd_name") == UPDATES_CMD_LIGHTS
                ]
                if updates_lights:
                    await self.async_update_lights(updates_lights)

            return self.data  # noqa: TRY300
        except camelib_errors.CameDomoticServerNotFoundError as e:
            LOGGER.warning("Server not found!")
            raise ConfigEntryError(e) from e
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

    async def async_update_lights(
        self, light_updates: list[dict] | None = None
    ) -> None:
        """Update lights data."""

        initialized: bool = False

        if light_updates and self.data.get(CONF_LIGHTS):
            came_lights: dict[int, camelib_models.Light] | None = self.data.get(
                CONF_LIGHTS
            )
            if came_lights is not None:
                initialized = True
                counter: int = 0
                for update in light_updates:
                    updated_light_id: int | None = update.get("act_id")
                    if updated_light_id is not None:
                        came_light: camelib_models.Light | None = came_lights.get(
                            updated_light_id
                        )
                        if came_light:
                            came_light.raw_data = update
                            self.data[CONF_LIGHTS][updated_light_id] = came_light
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

            if init_lights:
                lights_list: dict[int, camelib_models.Light] = {
                    light.act_id: light for light in init_lights
                }
                self.data[CONF_LIGHTS] = lights_list
                LOGGER.debug(
                    "[_async_update_data] Initialized %s light devices",
                    len(lights_list) if lights_list else 0,
                )
            else:
                LOGGER.info("No lights found in the server")


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
