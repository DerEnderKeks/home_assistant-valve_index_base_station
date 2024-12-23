"""Library to interact with Valve Index Base Stations."""

import asyncio
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from enum import Enum
from uuid import UUID

from bleak import (
    AdvertisementData,
    BleakGATTCharacteristic,
    BleakGATTServiceCollection,
    BLEDevice,
)
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
    retry_bluetooth_connection_error,
)
from habluetooth import BluetoothServiceInfoBleak

_LOGGER = logging.getLogger(__name__)

BLE_RETRY_ATTEMPTS = 3
MANUFACTURER_ID = 1373
NAME_PREFIX = "LHB-"

CHARACTERISTIC_UUID_MODEL_ID = "2a24"
CHARACTERISTIC_UUID_SERIAL_NUMBER = "2a25"
CHARACTERISTIC_UUID_SW_VERSION = "2a26"
CHARACTERISTIC_UUID_MANUFACTURER = "2a29"

CHARACTERISTIC_UUID_POWER = "00001525-1212-efde-1523-785feabcd124"
CHARACTERISTIC_UUID_IDENTIFY = "00008421-1212-efde-1523-785feabcd124"
CHARACTERISTIC_UUID_CHANNEL = "00001524-1212-efde-1523-785feabcd124"

CHANNEL_NUM_MIN = 1
CHANNEL_NUM_MAX = 16


def model_name(num: str) -> str:
    """Convert the model number to a name."""
    models = {
        "1004": "SteamVR Base Station 2.0",
    }

    if num in models:
        return models[num]

    return "Unknown"


def _is_basestation_device(info: BluetoothServiceInfoBleak) -> bool:
    return info.manufacturer_id == MANUFACTURER_ID and info.name.startswith(NAME_PREFIX)


def filter_discoveries(
    discoveries: Iterable[BluetoothServiceInfoBleak],
) -> Iterable[BluetoothServiceInfoBleak]:
    """Filter for discoveries that are Base Stations."""
    return [i for i in discoveries if _is_basestation_device(i)]


def _require_characteristic(
    services: BleakGATTServiceCollection, specifier: int | str | UUID
) -> BleakGATTCharacteristic:
    char = services.get_characteristic(specifier)
    if not char:
        msg = "Characteristic not found"
        raise ValueError(msg)
    return char


class BasestationStatePower(Enum):
    """Base Station power states."""

    SLEEPING = 0x00
    AWAKE = 0x01
    STANDBY = 0x02
    AWAKE_AFTER_SLEEPING = 0x09
    AWAKE_AFTER_STANDBY = 0x0B


@dataclass(frozen=True)
class BasestationState:
    """State of a Base Station."""

    power: BasestationStatePower = None
    channel: int = None
    sw_version: str = None


class BasestationAPI:
    """API to talk to a Base Station."""

    def __init__(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData | None = None
    ) -> None:
        """Initialize the Basestation API."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data

        self._client: BleakClientWithServiceCache | None = None
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._callbacks: list[Callable[[BasestationState], None]] = []

        self._state = BasestationState()
        self._manufacturer: str | None = None
        self._model_id: str | None = None
        self._serial_number: str | None = None

    @property
    def address(self) -> str:
        """Get the BLE MAC address."""
        return self._ble_device.address

    @property
    def name(self) -> str:
        """Get the name."""
        return self._ble_device.name or self._ble_device.address

    @property
    def manufacturer(self) -> str:
        """Get the manufacturer name."""
        return self._manufacturer

    @property
    def model(self) -> str:
        """Get the model name."""
        return model_name(self._model_id)

    @property
    def model_id(self) -> str:
        """Get the model number."""
        return self._model_id

    @property
    def serial_number(self) -> str:
        """Get the serial number."""
        return self._serial_number

    @property
    def sw_version(self) -> str:
        """Get the software version."""
        return self._state.sw_version

    @property
    def rssi(self) -> int | None:
        """Get the RSSI."""
        if self._advertisement_data:
            return self._advertisement_data.rssi
        return None

    @property
    def state(self) -> BasestationState:
        """Get the full state."""
        return self._state

    @property
    def is_on(self) -> bool:
        """Check if on."""
        return self._state.power not in [
            BasestationStatePower.STANDBY,
            BasestationStatePower.SLEEPING,
        ]

    @property
    def channel(self) -> int:
        """Get the current channel."""
        return self._state.channel

    def set_ble_device_and_advertisement_data(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        """Set the BLE device and advertisement data."""
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data

    async def update(self) -> BasestationState:
        """Update the state data."""
        _LOGGER.debug("%s (%s): Updating data", self.name, self.address)
        try:
            if (
                self._serial_number is None
            ):  # only initialise once, not expected to change
                self._model_id = (
                    await self._read_char(CHARACTERISTIC_UUID_MODEL_ID)
                ).decode()
                self._manufacturer = (
                    await self._read_char(CHARACTERISTIC_UUID_MANUFACTURER)
                ).decode()
                self._serial_number = (
                    await self._read_char(CHARACTERISTIC_UUID_SERIAL_NUMBER)
                ).decode()

            power = BasestationStatePower(
                (await self._read_char(CHARACTERISTIC_UUID_POWER))[0]
            )
            channel = int.from_bytes(await self._read_char(CHARACTERISTIC_UUID_CHANNEL))
            sw_version = (
                await self._read_char(CHARACTERISTIC_UUID_SW_VERSION)
            ).decode()
        finally:
            await self.disconnect()

        self._state = BasestationState(
            power=power,
            channel=channel,
            sw_version=sw_version,
        )

        _LOGGER.debug("%s (%s): Updated data: %s", self.name, self.address, self.state)
        return self.state

    async def set_power_state(self, power: BasestationStatePower) -> None:
        """Set the power state."""
        _LOGGER.debug(
            "%s (%s): Setting power state to %s", self.name, self.address, power
        )
        await self._write_char(
            CHARACTERISTIC_UUID_POWER,
            [power.value.to_bytes()],
            disconnect=True,
        )
        self._state = replace(self._state, power=power)
        self._fire_callbacks()

    async def set_power_on(self) -> None:
        """Turn on."""
        await self.set_power_state(power=BasestationStatePower.AWAKE)

    async def set_power_off(self) -> None:
        """Turn off (sleep)."""
        await self.set_power_state(power=BasestationStatePower.SLEEPING)

    async def set_channel(self, channel: int) -> None:
        """Set the channel."""
        if channel < CHANNEL_NUM_MIN or channel > CHANNEL_NUM_MAX:
            msg = "Invalid channel number"
            raise ValueError(msg)

        _LOGGER.debug(
            "%s (%s): Setting channel to %s", self.name, self.address, channel
        )
        await self._write_char(
            CHARACTERISTIC_UUID_CHANNEL, [channel.to_bytes()], disconnect=True
        )
        # Channel change will turn on the device automatically
        self._state = replace(
            self._state, channel=channel, power=BasestationStatePower.AWAKE
        )
        self._fire_callbacks()

    async def identify(self) -> None:
        """Trigger the identify action."""
        _LOGGER.debug("%s (%s): Identifying", self.name, self.address)
        await self._write_char(CHARACTERISTIC_UUID_IDENTIFY, [0x01.to_bytes()], disconnect=True)

        # Identify will turn on the device automatically
        self._state = replace(self._state, power=BasestationStatePower.AWAKE)
        self._fire_callbacks()

    async def connect(self) -> None:
        """Connect."""
        if self._client and self._client.is_connected:
            return

        async with self._connect_lock:
            if self._client and self._client.is_connected:
                return  # recheck while locked

            _LOGGER.debug("%s (%s): Connecting", self.name, self.address)
            client = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self.name,
                use_services_cache=True,
                ble_device_callback=lambda: self._ble_device,
            )

            self._client = client

    async def disconnect(self) -> None:
        """Disconnect."""
        async with self._connect_lock:
            client = self._client

            self._client = None

            _LOGGER.debug("%s (%s): Disconnecting", self.name, self.address)
            if client and client.is_connected:
                await client.disconnect()

    @retry_bluetooth_connection_error(BLE_RETRY_ATTEMPTS)
    async def _write_char(
        self,
        char: BleakGATTCharacteristic | int | str | UUID,
        commands: list[bytes],
        disconnect: bool = False,  # noqa: FBT001 FBT002
    ) -> None:
        _LOGGER.debug(
            "%s (%s): Writing characteristic %s: %s",
            self.name,
            self.address,
            char,
            [command.hex() for command in commands],
        )
        try:
            await self.connect()
            for command in commands:
                await self._client.write_gatt_char(char, command, response=False)
        finally:
            if disconnect:
                await self.disconnect()

    @retry_bluetooth_connection_error(BLE_RETRY_ATTEMPTS)
    async def _read_char(
        self,
        char: BleakGATTCharacteristic | int | str | UUID,
        disconnect: bool = False,  # noqa: FBT001 FBT002
    ) -> bytearray:
        _LOGGER.debug(
            "%s (%s): Reading characteristic %s",
            self.name,
            self.address,
            char,
        )
        try:
            await self.connect()
            read = await self._client.read_gatt_char(char)
        finally:
            if disconnect:
                await self.disconnect()

        _LOGGER.debug(
            "%s (%s): Read characteristic %s: %s",
            self.name,
            self.address,
            char,
            read,
        )
        return read

    def _fire_callbacks(self) -> None:
        for callback in self._callbacks:
            callback(self._state)

    def register_callback(
        self, callback: Callable[[BasestationState], None]
    ) -> Callable[[], None]:
        """Register callbacks to call when the state changes."""

        def unregister_callback() -> None:
            self._callbacks.remove(callback)

        self._callbacks.append(callback)
        return unregister_callback
