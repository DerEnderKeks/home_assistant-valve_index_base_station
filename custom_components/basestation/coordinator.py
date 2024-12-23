"""Base Station coordinator."""

import logging
from asyncio import timeout
from datetime import timedelta

from bleak_retry_connector import BLEAK_EXCEPTIONS
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import UPDATE_INTERVAL_SECONDS
from .lib import BasestationAPI, BasestationState

_LOGGER = logging.getLogger(__name__)


class BasestationCoordinator(DataUpdateCoordinator):
    """Valve Index Base Station Coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        api: BasestationAPI,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Valve Index Base Station",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
            always_update=False,
            config_entry=config_entry,
        )
        self.basestation_ble: BasestationAPI = api

    async def _async_update_data(self) -> BasestationState:
        try:
            async with timeout(10):
                return await self.basestation_ble.update()
        except Exception as ex:
            raise UpdateFailed(str(ex)) from ex
