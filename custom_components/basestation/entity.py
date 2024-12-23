from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import BasestationCoordinator


class BasestationEntity(CoordinatorEntity[BasestationCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: BasestationCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def unique_id(self) -> str:
        uid = dr.format_mac(self.coordinator.basestation_ble.address)
        if self.entity_description and self.entity_description.key:
            uid += f"_{self.entity_description.key}"

        return uid

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            connections={
                (
                    dr.CONNECTION_BLUETOOTH,
                    self.coordinator.basestation_ble.address,
                )
            },
            name=self.coordinator.basestation_ble.name,
            manufacturer=self.coordinator.basestation_ble.manufacturer,
            model_id=self.coordinator.basestation_ble.model_id,
            model=self.coordinator.basestation_ble.model,
            sw_version=self.coordinator.basestation_ble.sw_version,
            serial_number=self.coordinator.basestation_ble.serial_number,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.coordinator.basestation_ble.register_callback(
                lambda _: self._handle_coordinator_update()
            )
        )
        return await super().async_added_to_hass()
