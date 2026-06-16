import asyncio
import json
from collections.abc import Awaitable, Callable

from dbus_fast import PropertyAccess
from dbus_fast.service import ServiceInterface, dbus_property, method

from config import SERVICE_PATH, WIFI_CHAR_UUID
from constants import GATT_CHARACTERISTIC_IFACE


class WifiProvisioningCharacteristic(ServiceInterface):
    def __init__(self, apply_wifi: Callable[[str, str], Awaitable[None]]) -> None:
        super().__init__(GATT_CHARACTERISTIC_IFACE)
        self._apply_wifi = apply_wifi
        self.value = b""

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> "o":
        return SERVICE_PATH

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return WIFI_CHAR_UUID

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":
        return ["write"]

    @method()
    async def WriteValue(self, value: "ay", _options: "a{sv}") -> None:
        self.value = bytes(value)
        try:
            payload = json.loads(self.value.decode("utf-8"))
            ssid = payload.get("ssid")
            psk = payload.get("psk")
            if ssid and psk:
                print(f"Received WiFi provisioning data: SSID={ssid}, PSK={psk}")
                # asyncio.create_task(self._apply_wifi(ssid, psk))
        except Exception as e:
            print(f"Error processing WiFi provisioning data: {e}")
