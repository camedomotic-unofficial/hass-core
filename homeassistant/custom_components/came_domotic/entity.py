"""BlueprintEntity class."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_UNIQUE_ID
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, MANUFACTURER
from .coordinator import CameCoordinatorServerInfo, CameDataUpdateCoordinator


class CameDomoticEntity(CoordinatorEntity):
    """BlueprintEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: CameDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)

        unique_id: str = coordinator.config_entry.data.get(CONF_UNIQUE_ID, "")
        name: str = coordinator.config_entry.title
        server_info: CameCoordinatorServerInfo | None = (
            coordinator.server_info if coordinator.server_info else None
        )
        host: str = coordinator.config_entry.data.get(CONF_HOST, "")

        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = (
            DeviceInfo(
                identifiers={(DOMAIN, unique_id)},
                name=name,
                model=server_info.type,
                manufacturer=MANUFACTURER,
                configuration_url=f"http://{host}/index_setup.html" if host else None,
                serial_number=server_info.serial,
                sw_version=server_info.swver,
                hw_version=server_info.board,
            )
            if server_info
            else DeviceInfo(
                identifiers={(DOMAIN, unique_id)},
                name=name,
                manufacturer=MANUFACTURER,
                configuration_url=f"http://{host}/index_setup.html" if host else None,
            )
        )
