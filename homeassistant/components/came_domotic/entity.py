"""BlueprintEntity class."""

from __future__ import annotations

import came_domotic_unofficial.models as camelib_models

from homeassistant.const import CONF_DEVICE, CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, MANUFACTURER, create_entity_unique_id
from .coordinator import CameCoordinatorServerInfo, CameDataUpdateCoordinator


def create_entity_descriptor(id: int, name: str) -> EntityDescription:
    """Create a light entity description."""
    return EntityDescription(
        key=create_entity_unique_id(id, name),
        has_entity_name=True,
        name=name,
    )


class CameDomoticEntity(CoordinatorEntity):
    """BlueprintEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: CameDataUpdateCoordinator,
        came_entity: camelib_models.base.CameEntity | camelib_models.CameLight,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        name: str = (
            came_entity.name
            if isinstance(came_entity, camelib_models.CameLight)
            else coordinator.config_entry.title
        )
        came_id: int = (
            came_entity.act_id
            if isinstance(came_entity, camelib_models.CameLight)
            else 0
        )
        unique_id: str = create_entity_unique_id(came_id, name)
        server_info: CameCoordinatorServerInfo | None = coordinator.data.get(
            CONF_DEVICE
        )
        host: str = coordinator.config_entry.data.get(CONF_HOST, "")

        self._attr_unique_id = unique_id
        self._name: str = name
        self._api_entity: camelib_models.base.CameEntity = came_entity
        self.entity_description = create_entity_descriptor(came_id, name)
        self._attr_device_info = (
            DeviceInfo(
                identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
                name=coordinator.config_entry.title,
                model=f"Server type: {server_info.type}",
                manufacturer=MANUFACTURER,
                configuration_url=f"http://{host}/index_setup.html" if host else None,
                serial_number=server_info.serial,
                sw_version=server_info.swver,
                hw_version=server_info.board,
            )
            if server_info
            else DeviceInfo(
                identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
                name=coordinator.config_entry.title,
                manufacturer=MANUFACTURER,
                configuration_url=f"http://{host}/index_setup.html" if host else None,
            )
        )
