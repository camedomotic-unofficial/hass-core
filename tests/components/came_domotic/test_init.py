"""Tests for CAME Domotic config flow."""

from unittest.mock import AsyncMock, patch

import aiocamedomotic as camelib

from homeassistant.components import came_domotic
from homeassistant.components.came_domotic.const import (
    DOMAIN,
    SERVERINFO_BOARD,
    SERVERINFO_FEATURES,
    SERVERINFO_KEYCODE,
    SERVERINFO_SERIAL,
    SERVERINFO_SWVER,
    SERVERINFO_TYPE,
)
from homeassistant.components.came_domotic.coordinator import (
    CameDataUpdateCoordinator,
    CameEntryRuntimeData,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import FIXTURE_API_SERVER_INFO, FIXTURE_CONFIG_ENTRY

from tests.common import MockConfigEntry


async def test_setup_works(hass: HomeAssistant) -> None:
    """Test that we can set up a CAME server entry."""
    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_create",
            return_value=AsyncMock(),
        ) as mock_create_api,
        patch(
            "aiocamedomotic.CameDomoticAPI.async_get_server_info",
            return_value=None,
        ) as mock_server_info,
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=None,
        ) as mock_forward_entry_setups,
        patch(
            "homeassistant.config_entries.ConfigEntry.async_on_unload",
            return_value=None,
        ) as mock_async_on_unload,
        patch(
            "homeassistant.components.came_domotic.coordinator.CameDataUpdateCoordinator.async_config_entry_first_refresh",
            return_value=None,
        ) as mock_coordinator_refresh,
    ):
        assert len(hass.config_entries.async_entries(domain=DOMAIN)) == 0
        MockConfigEntry(
            domain=DOMAIN,
            unique_id=FIXTURE_CONFIG_ENTRY["unique_id"],
            data=FIXTURE_CONFIG_ENTRY["data"],
        ).add_to_hass(hass)
        assert await async_setup_component(hass, DOMAIN, {}) is True
        assert len(hass.config_entries.async_entries(domain=DOMAIN)) == 1

        # Ensure that the data are properly stored
        entry = hass.config_entries.async_entries(domain=DOMAIN)[0]
        assert isinstance(entry.runtime_data, CameEntryRuntimeData)
        coordinator = entry.runtime_data.coordinator
        assert isinstance(coordinator, CameDataUpdateCoordinator)
        assert coordinator.data[SERVERINFO_BOARD] == FIXTURE_API_SERVER_INFO.board
        assert coordinator.data[SERVERINFO_FEATURES] == FIXTURE_API_SERVER_INFO.list
        assert coordinator.data[SERVERINFO_KEYCODE] == FIXTURE_API_SERVER_INFO.keycode
        assert coordinator.data[SERVERINFO_SERIAL] == FIXTURE_API_SERVER_INFO.serial
        assert coordinator.data[SERVERINFO_SWVER] == FIXTURE_API_SERVER_INFO.swver
        assert coordinator.data[SERVERINFO_TYPE] == FIXTURE_API_SERVER_INFO.type

        # Ensure that the API is properly consumed
        mock_create_api.assert_called_once()
        mock_server_info.assert_not_called()

        mock_async_on_unload.assert_called()
        # Ensure that the setup is forwarded to the platforms
        mock_forward_entry_setups.assert_called_once()
        # Ensure that the coordinator is refreshed
        mock_coordinator_refresh.assert_called_once()


async def test_setup_with_no_config(hass: HomeAssistant) -> None:
    """Test that we do not set up any bridge."""
    assert await async_setup_component(hass, DOMAIN, {}) is True

    # No flows started
    assert len(hass.config_entries.flow.async_progress()) == 0

    # No configs stored
    assert len(hass.config_entries.async_entries(domain=DOMAIN)) == 0


async def test_unload_entry(hass: HomeAssistant) -> None:
    """Test being able to unload an entry."""
    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_create",
            return_value=camelib.CameDomoticAPI(auth=None),
        ),
        patch(
            "aiocamedomotic.CameDomoticAPI.async_dispose",
        ) as mock_dispose,
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id=FIXTURE_CONFIG_ENTRY["unique_id"],
            data=FIXTURE_CONFIG_ENTRY["data"],
        )
        entry.add_to_hass(hass)
        assert await async_setup_component(hass, DOMAIN, {}) is True
        assert isinstance(entry.runtime_data, CameEntryRuntimeData)

        assert await came_domotic.async_unload_entry(hass, entry)

        mock_dispose.assert_called_once()
        assert entry.runtime_data is None


async def test_reload_entry(hass: HomeAssistant) -> None:
    """Test being able to reload an entry."""
    assert await async_setup_component(hass, DOMAIN, {}) is True

    with (
        patch(
            "homeassistant.components.came_domotic.async_unload_entry",
            return_value=None,
        ) as mock_unload_entry,
        patch(
            "homeassistant.components.came_domotic.async_setup_entry",
            return_value=None,
        ) as mock_setup_entry,
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id=FIXTURE_CONFIG_ENTRY["unique_id"],
            data=FIXTURE_CONFIG_ENTRY["data"],
        )
        entry.add_to_hass(hass)
        await came_domotic.async_reload_entry(hass, entry)

        mock_unload_entry.assert_called_once_with(hass, entry)
        mock_setup_entry.assert_called_once_with(hass, entry)
