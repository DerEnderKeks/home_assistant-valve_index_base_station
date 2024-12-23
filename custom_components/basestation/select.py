"""Base Station selects."""

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
    """Set up all Base Station selects."""
    coordinator: BasestationCoordinator = config_entry.runtime_data
    async_add_entities([BasestationChannelSelect(coordinator)])


class BasestationChannelSelect(BasestationEntity, SelectEntity):
    """Base Station channel select."""

    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:list-box"

    def __init__(
        self,
        coordinator: BasestationCoordinator,
    ) -> None:
        """Initialize the channel select."""
        super().__init__(coordinator)
        self.entity_description = SelectEntityDescription(
            key="channel",
            name="Channel",
        )
        self._attr_options = [str(i) for i in range(1, 16)]

    @property
    def current_option(self) -> str:
        """Get the current channel."""
        return str(self.coordinator.basestation_ble.channel)

    async def async_select_option(self, option: str) -> None:
        """Set the selected channel."""
        await self.coordinator.basestation_ble.set_channel(int(option))
