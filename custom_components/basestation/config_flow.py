"""Base Station config flow."""

import logging
from typing import Any

import voluptuous as vol
from bleak_retry_connector import BLEAK_EXCEPTIONS
from bluetooth_data_tools import human_readable_name
from habluetooth import BluetoothServiceInfoBleak
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN
from .lib import BasestationAPI, filter_discoveries

_LOGGER = logging.getLogger(__name__)


class BasestationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Base Station config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Bluetooth step."""
        await self.async_set_unique_id(format_mac(discovery_info.address))
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": human_readable_name(
                None, discovery_info.name, discovery_info.address
            )
        }
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """User step."""
        error: str | None = None

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery_info = self._discovered_devices[address]
            local_name = discovery_info.name
            await self.async_set_unique_id(
                format_mac(discovery_info.address), raise_on_progress=False
            )
            self._abort_if_unique_id_configured()
            basestation_ble = BasestationAPI(discovery_info.device)
            try:
                await basestation_ble.update()
            except BLEAK_EXCEPTIONS:
                error = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error")
                error = "unknown"
            else:
                return self.async_create_entry(
                    title=local_name,
                    data={
                        CONF_ADDRESS: discovery_info.address,
                    },
                )

        if discovery := self._discovery_info:
            self._discovered_devices[format_mac(discovery.address)] = discovery
        else:
            current_addresses = self._async_current_ids()
            for discovery in filter_discoveries(
                async_discovered_service_info(self.hass)
            ):
                discovered_address = format_mac(discovery.address)
                if (
                    discovered_address in current_addresses
                    or discovered_address in self._discovered_devices
                ):
                    continue

                self._discovered_devices[discovered_address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        format_mac(service_info.address): human_readable_name(
                            None, service_info.name, service_info.address
                        )
                        for service_info in self._discovered_devices.values()
                    }
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors={"base": error},
        )
