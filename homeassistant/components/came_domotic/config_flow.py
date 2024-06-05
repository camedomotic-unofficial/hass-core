"""Adds config flow for CAME Domotic."""

from __future__ import annotations

from typing import Any

import came_domotic_unofficial as camelib
import came_domotic_unofficial.errors as camelib_err

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_UNIQUE_ID,
    CONF_USERNAME,
)
from homeassistant.helpers import aiohttp_client as client

from .const import DOMAIN, LOGGER, create_unique_id, get_form_schema


@config_entries.HANDLERS.register(DOMAIN)
class CameDomoticConfigFlow(config_entries.ConfigFlow):
    """Config flow for CAME Domotic."""

    VERSION = 1
    MINOR_VERSION = 0

    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_create_came_entry(
        self, user_input: dict[str, Any], *, errors: dict[str, str]
    ) -> config_entries.ConfigFlowResult:
        """Create a config entry for the CAME Domotic server instance."""
        try:
            async with await camelib.CameDomoticAPI.async_create(
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                websession=client.async_get_clientsession(self.hass),
            ) as api:
                LOGGER.debug("[async_create_came_entry] API client created")

                server_info = await api.async_get_server_info()
                LOGGER.debug("[async_create_came_entry] Server info: %s", server_info)

                if server_info:
                    already_configured_entry = await self.async_set_unique_id(
                        server_info.keycode
                    )
                    if already_configured_entry:
                        LOGGER.debug(
                            "[async_create_came_entry] Already configured, aborting"
                        )
                        return self.async_abort(reason="already_configured")

                    LOGGER.debug("[async_create_came_entry] Creating config entry")
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        description="This is the config entry description injected on setup",
                        data={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_UNIQUE_ID: create_unique_id(
                                user_input[CONF_USERNAME], server_info.keycode
                            ),
                            # CONF_MAC: format_mac(server_info.keycode),
                        },
                    )
                # Consider server_info is None as an unexpected server response,
                # since, in case of errors, async_get_server_info should raise an
                # exception, not return None
                errors["base"] = "unexpected_server_response"
                return self.async_abort(reason="unexpected_server_response")
        except camelib_err.CameDomoticServerNotFoundError as err:
            LOGGER.debug("Invalid host error: %s", err)
            errors["base"] = "server_not_found"
            return self.async_abort(reason="server_not_found")
        except camelib_err.CameDomoticAuthError as err:
            LOGGER.debug("Invalid credentials error: %s", err)
            errors["base"] = "auth"
            return self.async_abort(reason="auth")
        except camelib_err.CameDomoticError as err:
            LOGGER.debug("CAME Domotic generic error: %s", err)
            errors["base"] = "unknown"
            return self.async_abort(reason="unknown")
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unexpected error")
            errors["base"] = "unknown"
            return self.async_abort(reason="unknown")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return await self.async_create_came_entry(
                user_input=user_input, errors=errors
            )

        data_schema = get_form_schema(self.hass, user_input)

        LOGGER.debug("[async_step_user] Showing user step form")
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
