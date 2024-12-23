"""The Valve Index Base Station integration."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothCallbackMatcher, BluetoothChange
from homeassistant.components.bluetooth.match import ADDRESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, callback

from .coordinator import BasestationCoordinator
from .lib import BasestationAPI

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SELECT, Platform.SWITCH]

type BasestationConfigEntry = ConfigEntry[BasestationCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BasestationConfigEntry) -> bool:
    """Set up config entry."""
    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable=True
    )

    basestation_ble = BasestationAPI(ble_device)

    @callback
    def _async_update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        _: BluetoothChange,
    ) -> None:
        basestation_ble.set_ble_device_and_advertisement_data(
            service_info.device, service_info.advertisement
        )

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_update_ble,
            BluetoothCallbackMatcher({ADDRESS: address}),
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )

    entry.runtime_data = coordinator = BasestationCoordinator(
        hass, entry, basestation_ble
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BasestationConfigEntry
) -> bool:
    """Unload callback."""
    await entry.runtime_data.basestation_ble.disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
