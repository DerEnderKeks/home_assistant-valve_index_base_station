"""Base Station switches."""

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
    _: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all Base Station switches."""
    coordinator: BasestationCoordinator = config_entry.runtime_data
    async_add_entities([BasestationPowerSwitch(coordinator)])


class BasestationPowerSwitch(BasestationEntity, SwitchEntity):
    """Base Station power switch."""

    def __init__(
        self,
        coordinator: BasestationCoordinator,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(
            key="power",
            name="Power",
            device_class=SwitchDeviceClass.SWITCH,
        )

    @property
    def is_on(self) -> bool:
        """Return true if Base Station is on."""
        return self.coordinator.basestation_ble.is_on

    async def async_turn_off(self, **_: Any) -> None:
        """Turn Base Station off."""
        await self.coordinator.basestation_ble.set_power_off()

    async def async_turn_on(self, **_: Any) -> None:
        """Turn Base Station on."""
        await self.coordinator.basestation_ble.set_power_on()
