"""Tests for CAME Domotic entity classes."""

from unittest.mock import patch

import aiocamedomotic.models as camelib_models
import pytest

from homeassistant.components.came_domotic.const import UPDATES_CMD_LIGHTS
from homeassistant.components.came_domotic.coordinator import CameDataUpdateCoordinator
from homeassistant.components.came_domotic.entity import CameLight
from homeassistant.components.light import ColorMode
from homeassistant.const import CONF_LIGHTS
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.fixture
def mock_api_light() -> camelib_models.Light:
    """Mock a CAME light."""
    return camelib_models.Light(
        raw_data={
            "cmd_name": UPDATES_CMD_LIGHTS,
            "act_id": 1,
            "name": "light_ChQQs",
            "status": camelib_models.LightStatus.ON,
            "type": camelib_models.LightType.DIMMER,
            "perc": 80,
        },
        auth=None,
    )


def test_came_light_init(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,
    mock_api_light: camelib_models.Light,
) -> None:
    """Test CameLight class initialization."""
    mock_coordinator.config_entry = MockConfigEntry()
    came_light = CameLight(mock_coordinator, mock_api_light)

    assert came_light.name == "light_ChQQs"
    assert came_light.brightness == int(0.8 * 255)
    assert came_light.is_on is True
    assert came_light.color_mode == ColorMode.BRIGHTNESS
    assert came_light.supported_color_modes == {ColorMode.BRIGHTNESS}
    assert came_light.came_id == 1
    assert came_light.unique_id == "came_1_light_chqqs"


async def test_came_light_turn_on_off(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,
    mock_api_light: camelib_models.Light,
) -> None:
    """Test CameLight async_turn_on and async_turn_off methods."""
    mock_coordinator.config_entry = MockConfigEntry()
    came_light = CameLight(mock_coordinator, mock_api_light)
    came_light.hass = hass

    with patch("aiocamedomotic.models.Light.async_set_status") as mock_set_status:
        await came_light.async_turn_on(brightness=153)  # 60% of 255
        mock_set_status.assert_called_once_with(camelib_models.LightStatus.ON, 60)

        await came_light.async_turn_off()
        mock_set_status.assert_called_with(camelib_models.LightStatus.OFF)
        assert mock_set_status.call_count == 2


async def test_came_light_set_brightness(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,
    mock_api_light: camelib_models.Light,
) -> None:
    """Test CameLight async_set_brightness method."""
    mock_coordinator.config_entry = MockConfigEntry()
    came_light = CameLight(mock_coordinator, mock_api_light)
    came_light.hass = hass

    with patch("aiocamedomotic.models.Light.async_set_status") as mock_set_status:
        await came_light.async_set_brightness(brightness=153)  # 60% of 255
        mock_set_status.assert_called_once_with(camelib_models.LightStatus.ON, 60)

        await came_light.async_set_brightness(brightness=0)
        mock_set_status.assert_called_with(camelib_models.LightStatus.OFF)
        assert mock_set_status.call_count == 2


async def test_came_light_update(
    hass: HomeAssistant,
    mock_coordinator: CameDataUpdateCoordinator,
    mock_api_light: camelib_models.Light,
) -> None:
    """Test CameLight async_update method."""
    mock_coordinator.config_entry = MockConfigEntry()
    mock_coordinator.data[CONF_LIGHTS] = None
    came_light = CameLight(mock_coordinator, mock_api_light)
    with (
        patch("aiocamedomotic.CameDomoticAPI.async_get_updates", return_value=None),
        patch("aiocamedomotic.CameDomoticAPI.async_get_lights", return_value=None),
        patch(
            "homeassistant.components.came_domotic.coordinator.CameDataUpdateCoordinator.async_update",
            return_value=None,
        ),  # as mock_refresh,
    ):
        await came_light.async_update()
        # mock_refresh.assert_called_once()
