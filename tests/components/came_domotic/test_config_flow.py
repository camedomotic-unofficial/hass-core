"""Tests for CAME Domotic config flow."""

from unittest.mock import AsyncMock, patch

import aiocamedomotic as camelib
import aiocamedomotic.errors as camelib_err

from homeassistant import config_entries
from homeassistant.components.came_domotic.const import CONF_NAME, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.selector import TextSelector

from . import FIXTURE_API_SERVER_INFO, FIXTURE_CONFIG_ENTRY, FIXTURE_USER_INPUT

from tests.common import MockConfigEntry


async def test_user_show_form(hass: HomeAssistant) -> None:
    """Test that a form with correct schema is served when no input is provided."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Ensure that the schema is correct
    s = result["data_schema"].schema
    isinstance(s["host"], TextSelector)
    isinstance(s["username"], TextSelector)
    isinstance(s["password"], TextSelector)
    isinstance(s["name"], TextSelector)

    # Ensure that the password field is obfuscated
    assert s["password"].config["type"] == "password"


async def test_user_create_entry(hass: HomeAssistant) -> None:
    """Test registering an integration and finishing flow works."""
    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_create",
            return_value=camelib.CameDomoticAPI(auth=None),
        ) as mock_create_api,
        patch(
            "aiocamedomotic.CameDomoticAPI.async_get_server_info",
            return_value=FIXTURE_API_SERVER_INFO,
        ) as mock_server_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=FIXTURE_USER_INPUT,
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == FIXTURE_USER_INPUT[CONF_NAME]
        assert result["context"]["unique_id"] == FIXTURE_CONFIG_ENTRY["unique_id"]
        assert result["data"] == FIXTURE_CONFIG_ENTRY["data"]

        mock_create_api.assert_called()
        mock_server_info.assert_called_once()


async def test_user_uniqueid_already_exists(hass: HomeAssistant) -> None:
    """Test that a flow is aborted if the unique_id already exists."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_CONFIG_ENTRY["unique_id"],
        data=FIXTURE_CONFIG_ENTRY["data"],
    ).add_to_hass(hass)

    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_create",
            return_value=camelib.CameDomoticAPI(auth=None),
        ),
        patch(
            "aiocamedomotic.CameDomoticAPI.async_get_server_info",
            return_value=FIXTURE_API_SERVER_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=FIXTURE_USER_INPUT,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_user_api_errors(hass: HomeAssistant) -> None:
    """Test that a flow is properly aborted if the API raises an error."""
    # Server not found
    with patch(
        "aiocamedomotic.CameDomoticAPI.async_create",
        side_effect=camelib_err.CameDomoticServerNotFoundError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=FIXTURE_USER_INPUT,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "server_not_found"

    with patch(
        "aiocamedomotic.CameDomoticAPI.async_create",
        return_value=camelib.CameDomoticAPI(auth=None),
    ):
        # Authentication error
        with patch(
            "aiocamedomotic.CameDomoticAPI.async_get_server_info",
            side_effect=camelib_err.CameDomoticAuthError,
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data=FIXTURE_USER_INPUT,
            )
            assert result["type"] is FlowResultType.ABORT
            assert result["reason"] == "auth"

        # Other server error
        with patch(
            "aiocamedomotic.CameDomoticAPI.async_get_server_info",
            side_effect=camelib_err.CameDomoticServerError,
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_USER},
                data=FIXTURE_USER_INPUT,
            )
            assert result["type"] is FlowResultType.ABORT
            assert result["reason"] == "unknown"


async def test_user_flow_errors(hass: HomeAssistant) -> None:
    """Test that a flow is properly aborted if the flow raises an error."""
    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_create",
            return_value=AsyncMock(),
        ),
        patch(
            "aiocamedomotic.CameDomoticAPI.async_get_server_info",
            return_value=FIXTURE_API_SERVER_INFO,
        ),
        patch(
            "homeassistant.components.came_domotic.config_flow.CameDomoticConfigFlow.async_create_entry",
            side_effect=Exception,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=FIXTURE_USER_INPUT,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "unknown"
