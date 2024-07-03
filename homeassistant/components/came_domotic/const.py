"""Constants for came_domotic."""

from logging import Logger, getLogger
import string
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

LOGGER: Logger = getLogger(__name__)

ATTRIBUTION = "CAME Unofficial API team"
DOMAIN = "came_domotic"
MANUFACTURER = "CAME S.p.A."
NAME = "CAME Domotic"
OUI_CAMEBPT = "001CB2"  # MAC Address prefix for BPT S.p.A.
VERSION = "0.1.0"

# Features supported by the CAME Domotic API
FEATURE_LIGHTS = "lights"
FEATURE_OPENINGS = "openings"
FEATURE_THERMOREGULATION = "thermoregulation"
FEATURE_SCENARIOS = "scenarios"
FEATURE_DIGITALIN = "digitalin"
FEATURE_ENERGY = "energy"
FEATURE_LOADSCTRL = "loadsctrl"

REQUEST_REFRESH_DELAY = 2.0
UPDATE_INTERVAL_SECS = 10

UPDATES_CMD_LIGHTS = "light_switch_ind"

SERVERINFO_BOARD = "camesi_board"
SERVERINFO_FEATURES = "camesi_features"
SERVERINFO_KEYCODE = "camesi_keycode"
SERVERINFO_SERIAL = "camesi_serial"
SERVERINFO_SWVER = "camesi_swver"
SERVERINFO_TYPE = "camesi_type"


def utils_normalize_string(value: str) -> str:
    """Normalize a string."""
    # Create a translation table
    keep_chars = string.ascii_letters + string.digits + " _-"
    remove_chars = "".join(set(string.printable) - set(keep_chars))
    translation_table = str.maketrans(" ", "_", remove_chars)

    # Return the normalized the string
    return value.translate(translation_table).lower()


def get_form_schema(
    hass: HomeAssistant,
    input_data: dict[str, Any] | None = None,
) -> vol.Schema:
    """Return the data schema for the user form."""
    # Specify items in the order they are to be displayed in the UI
    return vol.Schema(
        {
            vol.Required(
                CONF_HOST,
                description={
                    "suggested_value": (input_data or {}).get(CONF_HOST, "192.168.1.3")
                },
            ): str,
            vol.Required(
                CONF_USERNAME, default=(input_data or {}).get(CONF_USERNAME, "admin")
            ): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
            ),
            vol.Required(
                CONF_PASSWORD, default=(input_data or {}).get(CONF_PASSWORD, "admin")
            ): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
            vol.Optional(
                CONF_NAME,
                default=(input_data or {}).get(CONF_NAME, hass.config.location_name),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        }
    )


def create_entry_unique_id(username: str, keycode: str) -> str:
    """Create a unique ID for a CAME Domotic config entry.

    The unique ID is a combination of the username and host, so that a user can have
    multiple config entries on the same host if the username if different (e.g. if
    different accounts on the same CAME Domotic system see different devices).

    Args:
        username (str): Username.
        keycode (str): Keycode of the CAME Domotic system.

    Returns:
        str: Unique ID of the config entry.

    """
    return f"{username}@{keycode}"


def create_entity_unique_id(id, name):
    """Create a unique ID for a CameDomoticEntity entity."""
    return f"came_{id}_{utils_normalize_string(name)}"


CAME_BASIC_FORM_SCHEMA = {
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Optional(CONF_NAME): str,
}
