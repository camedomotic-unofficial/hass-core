"""Tests for the CAME Domotic component."""

from datetime import timedelta
from unittest.mock import Mock

import aiocamedomotic as camelib
import pytest

from homeassistant.components.came_domotic.const import (
    DOMAIN,
    SERVERINFO_BOARD,
    SERVERINFO_FEATURES,
    SERVERINFO_KEYCODE,
    SERVERINFO_SERIAL,
    SERVERINFO_SWVER,
    SERVERINFO_TYPE,
)
from homeassistant.components.came_domotic.coordinator import CameDataUpdateCoordinator
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

FIXTURE_API_SERVER_INFO = Mock(
    keycode="0000FFFF9999AAAA",
    list=[
        "lights",
        "openings",
        "thermoregulation",
        "scenarios",
        "digitalin",
        "energy",
        "loadsctrl",
    ],
    serial="0011ffee",
    board="3",
    swver="1.2.3",
    type="0",
)


FIXTURE_USER_INPUT = {
    CONF_USERNAME: "my_username",
    CONF_PASSWORD: "my_password",
    CONF_HOST: "1.2.3.4",
    CONF_NAME: "my_name",
}

FIXTURE_CONFIG_ENTRY = {
    "entry_id": "1",
    "unique_id": f"{FIXTURE_USER_INPUT[CONF_USERNAME]}@{FIXTURE_API_SERVER_INFO.keycode}",
    "domain": DOMAIN,
    "title": FIXTURE_USER_INPUT[CONF_NAME],
    "data": {
        CONF_HOST: FIXTURE_USER_INPUT[CONF_HOST],
        CONF_USERNAME: FIXTURE_USER_INPUT[CONF_USERNAME],
        CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD],
        SERVERINFO_BOARD: FIXTURE_API_SERVER_INFO.board,
        SERVERINFO_FEATURES: FIXTURE_API_SERVER_INFO.list,
        SERVERINFO_KEYCODE: FIXTURE_API_SERVER_INFO.keycode,
        SERVERINFO_SERIAL: FIXTURE_API_SERVER_INFO.serial,
        SERVERINFO_SWVER: FIXTURE_API_SERVER_INFO.swver,
        SERVERINFO_TYPE: FIXTURE_API_SERVER_INFO.type,
    },
    # "options": {CONF_READ_ONLY: False},
    # "source": config_entries.SOURCE_USER,
}


@pytest.fixture
def mock_coordinator(
    hass: HomeAssistant,
) -> CameDataUpdateCoordinator:
    """Mock CameDataUpdateCoordinator fixture."""
    return CameDataUpdateCoordinator(
        hass=hass,
        client=camelib.CameDomoticAPI(auth=None),
        name="DEFAULT_NAME",
        update_interval=timedelta(seconds=60),
        always_update=False,
    )
