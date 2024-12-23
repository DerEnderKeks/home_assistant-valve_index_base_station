"""Base Station buttons."""

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
    _: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all button entities."""
    coordinator: BasestationCoordinator = config_entry.runtime_data
    async_add_entities([BasestationIdentifyButton(coordinator)])


class BasestationIdentifyButton(BasestationEntity, ButtonEntity):
    """Base Station identify button."""

    def __init__(
        self,
        coordinator: BasestationCoordinator,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.entity_description = ButtonEntityDescription(
            key="identify",
            name="Identify",
            device_class=ButtonDeviceClass.IDENTIFY,
        )

    async def async_press(self) -> None:
        """Trigger the identify action."""
        await self.coordinator.basestation_ble.identify()
