from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BasestationCoordinator
from .entity import BasestationEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BasestationCoordinator = config_entry.runtime_data
    async_add_entities([BasestationIdentifyButton(coordinator)])


class BasestationIdentifyButton(BasestationEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: BasestationCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = ButtonEntityDescription(
            key="identify",
            name="Identify",
            device_class=ButtonDeviceClass.IDENTIFY,
        )

    async def async_press(self) -> None:
        await self.coordinator.basestation_ble.identify()
