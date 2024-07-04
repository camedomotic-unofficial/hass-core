"""Tests for CAME Domotic config flow."""

from datetime import timedelta
from unittest.mock import patch

import aiocamedomotic as camelib
import aiocamedomotic.models as camelib_models

from homeassistant.components.came_domotic.const import UPDATES_CMD_LIGHTS
from homeassistant.components.came_domotic.coordinator import (
    CameCoordinatorData,
    CameDataUpdateCoordinator,
    CameEntryRuntimeData,
)
from homeassistant.const import CONF_LIGHTS
from homeassistant.core import HomeAssistant

from . import mock_coordinator  # noqa: F401


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


async def test_coord_update_data_lights(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,  # noqa: F811
) -> None:
    """Test coordinator async_update method."""
    mock_coordinator.data[CONF_LIGHTS] = {
        1: camelib_models.Light(
            raw_data={
                "act_id": 1,
                "name": "light_ChQQs",
                "status": camelib_models.LightStatus.OFF,
                "type": "STEP_STEP",
            },
            auth=None,
        ),
        3: camelib_models.Light(
            raw_data={
                "act_id": 3,
                "name": "light_xLKSn",
                "status": camelib_models.LightStatus.OFF,
                "perc": 70,
                "type": "DIMMER",
            },
            auth=None,
        ),
        5: camelib_models.Light(
            raw_data={
                "act_id": 5,
                "name": "light_xLKSn",
                "status": camelib_models.LightStatus.OFF,
                "type": "STEP_STEP",
            },
            auth=None,
        ),
    }
    with patch(
        "aiocamedomotic.CameDomoticAPI.async_get_updates",
        return_value=camelib_models.UpdateList(
            raw_data={
                "result": [
                    {
                        "cmd_name": UPDATES_CMD_LIGHTS,
                        "act_id": 1,
                        "name": "light_ChQQs",
                        "status": camelib_models.LightStatus.ON,
                        "type": camelib_models.LightType.STEP_STEP,
                    },
                    {
                        "cmd_name": UPDATES_CMD_LIGHTS,
                        "act_id": 3,
                        "name": "light_xLKSn",
                        "status": camelib_models.LightStatus.ON,
                        "perc": 50,
                        "type": camelib_models.LightType.DIMMER,
                    },
                    {
                        "cmd_name": "other_update",
                        "act_id": 99,
                    },
                ],
            }
        ),
    ) as mocked_updates:
        result: CameCoordinatorData = await mock_coordinator.async_update()
        light1: camelib_models.Light = result[CONF_LIGHTS][1]
        light3: camelib_models.Light = result[CONF_LIGHTS][3]
        light5: camelib_models.Light = result[CONF_LIGHTS][5]

        mocked_updates.assert_called_once()
        assert light1.status == camelib_models.LightStatus.ON
        assert light3.status == camelib_models.LightStatus.ON
        assert light3.perc == 50
        assert light5.status == camelib_models.LightStatus.OFF  # Unchanged


async def test_coord_update_no_updates_lights(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,  # noqa: F811
) -> None:
    """Test coordinator async_update method."""
    mock_coordinator.data[CONF_LIGHTS] = {
        1: camelib_models.Light(
            raw_data={
                "act_id": 1,
                "name": "light_ChQQs",
                "status": camelib_models.LightStatus.OFF,
                "type": "STEP_STEP",
            },
            auth=None,
        ),
        3: camelib_models.Light(
            raw_data={
                "act_id": 3,
                "name": "light_xLKSn",
                "status": camelib_models.LightStatus.OFF,
                "perc": 70,
                "type": "DIMMER",
            },
            auth=None,
        ),
        5: camelib_models.Light(
            raw_data={
                "act_id": 5,
                "name": "light_xLKSn",
                "status": camelib_models.LightStatus.OFF,
                "type": "STEP_STEP",
            },
            auth=None,
        ),
    }
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


async def test_coord_update_lights_cache_empty(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,  # noqa: F811
) -> None:
    """Test coordinator async_update_lights method when the lights cache is empty."""
    with (
        patch(
            "aiocamedomotic.CameDomoticAPI.async_get_lights",
            return_value=[
                camelib_models.Light(
                    raw_data={
                        "act_id": 1,
                        "name": "light_ChQQs",
                        "status": camelib_models.LightStatus.OFF,
                        "type": "STEP_STEP",
                    },
                    auth=None,
                ),
                camelib_models.Light(
                    raw_data={
                        "act_id": 3,
                        "name": "light_xLKSn",
                        "status": camelib_models.LightStatus.OFF,
                        "perc": 70,
                        "type": "DIMMER",
                    },
                    auth=None,
                ),
            ],
        ) as mocked_get_lights,
        patch("aiocamedomotic.CameDomoticAPI.async_get_updates", return_value=None),
    ):
        mock_coordinator.data[CONF_LIGHTS] = None
        await mock_coordinator.async_update()

        # Assert that the lights cache has been initialized
        mocked_get_lights.assert_called_once()
        assert len(mock_coordinator.data.get(CONF_LIGHTS)) == 2


async def test_cameentryruntimedata_initialization(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,  # noqa: F811
) -> None:
    """Test the initialization of CameEntryRuntimeData."""
    runtime_data = CameEntryRuntimeData(coordinator=mock_coordinator)

    assert runtime_data.coordinator == mock_coordinator


async def test_camecoordinatordata_initialization(hass: HomeAssistant) -> None:
    """Test accessing the coordinator attribute of CameEntryRuntimeData."""
    coordinator_data = CameCoordinatorData()
    coordinator_data["test1"] = "test1"
    coordinator_data["test2"] = 2
    coordinator_data["test3"] = {"test3": "test3"}

    assert coordinator_data["test1"] == "test1"
    assert coordinator_data["test2"] == 2
    assert coordinator_data["test3"] == {"test3": "test3"}
