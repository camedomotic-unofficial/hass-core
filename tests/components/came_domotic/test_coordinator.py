"""Tests for CAME Domotic config flow."""

from datetime import timedelta
from unittest.mock import patch

import aiocamedomotic as camelib
import aiocamedomotic.models as camelib_models
import pytest

from homeassistant.components.came_domotic.const import UPDATES_CMD_LIGHTS
from homeassistant.components.came_domotic.coordinator import (
    CameCoordinatorData,
    CameDataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_coordinator(
    hass: HomeAssistant,
):
    """Mock CameDataUpdateCoordinator fixture."""
    return CameDataUpdateCoordinator(
        hass=hass,
        client=camelib.CameDomoticAPI(auth=None),
        name="DEFAULT_NAME",
        update_interval=timedelta(seconds=60),
        always_update=False,
    )


async def test_coordinator_init(hass: HomeAssistant) -> None:
    """Test coordinator init method."""
    api = camelib.CameDomoticAPI(auth=None)
    coordinator = CameDataUpdateCoordinator(
        hass=hass,
        client=api,
        name="DEFAULT_NAME",
        update_interval=timedelta(seconds=60),
        always_update=False,
    )

    assert coordinator.hass == hass
    assert coordinator.client == api
    assert coordinator.name == "DEFAULT_NAME"
    assert coordinator.update_interval == timedelta(seconds=60)
    assert coordinator.always_update is False
    assert isinstance(coordinator.data, CameCoordinatorData)


async def test_coord_update_data(
    hass: HomeAssistant, mock_coordinator: CameDataUpdateCoordinator
) -> None:
    """Test coordinator async_update method."""
    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_get_updates",
            return_value=camelib_models.UpdateList(
                {
                    "result": [
                        {
                            "cmd_name": UPDATES_CMD_LIGHTS,
                            "act_id": 1,
                            "name": "light_ChQQs",
                        },
                        {
                            "cmd_name": "other_update",
                            "act_id": 99,
                        },
                    ],
                }
            ),
        ) as mocked_updates,
        patch(
            "homeassistant.components.came_domotic.CameDataUpdateCoordinator.async_update_lights",
            return_value=None,
        ) as mocked_update_lights,
    ):
        await mock_coordinator.async_update()

        mocked_updates.assert_called_once()
        mocked_update_lights.assert_called_once()


async def test_coord_update_no_lights(
    hass: HomeAssistant, mock_coordinator: CameDataUpdateCoordinator
) -> None:
    """Test coordinator async_update method."""
    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_get_updates",
            return_value=camelib_models.UpdateList(
                {
                    "result": [
                        {
                            "cmd_name": "other_update",
                            "act_id": 99,
                        },
                    ],
                }
            ),
        ) as mocked_updates,
        patch(
            "homeassistant.components.came_domotic.CameDataUpdateCoordinator.async_update_lights",
            return_value=None,
        ) as mocked_update_lights,
    ):
        await mock_coordinator.async_update()

        mocked_updates.assert_called_once()
        mocked_update_lights.assert_not_called()


async def test_coord_update_lights(hass: HomeAssistant) -> None:
    """Test coordinator async_update_lights method."""


async def test_coord_update_lights_cache_empty(hass: HomeAssistant) -> None:
    """Test coordinator async_update_lights method when the lights cache is empty."""
