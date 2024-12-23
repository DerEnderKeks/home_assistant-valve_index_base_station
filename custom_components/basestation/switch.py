from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
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
    async_add_entities([BasestationPowerSwitch(coordinator)])


class BasestationPowerSwitch(BasestationEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: BasestationCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(
            key="power",
            name="Power",
            device_class=SwitchDeviceClass.SWITCH,
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.basestation_ble.is_on

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.basestation_ble.set_power_off()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.basestation_ble.set_power_on()
