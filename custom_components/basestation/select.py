from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
    async_add_entities([BasestationChannelSelect(coordinator)])


class BasestationChannelSelect(BasestationEntity, SelectEntity):
    _attr_entity_registry_enabled_default = False
    _attr_options = list(map(lambda i: str(i), range(1, 16)))
    _attr_icon = "mdi:list-box"

    def __init__(
        self,
        coordinator: BasestationCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = SelectEntityDescription(
            key="channel",
            name="Channel",
        )

    @property
    def current_option(self) -> str:
        return str(self.coordinator.basestation_ble.channel)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.basestation_ble.set_channel(int(option))
