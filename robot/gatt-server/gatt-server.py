#!/usr/bin/env python3
"""BlueZ GATT service + LE advertisement for Debian/Linux."""

import asyncio
import signal
import socket
from typing import Any

from dbus_fast import BusType, PropertyAccess, Variant
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, dbus_property, method
from characteristics import (
    NetworkStatusCharacteristic,
    WifiProvisioningCharacteristic,
)
from config import (
    ADV_MAX_INTERVAL_MS,
    ADV_MIN_INTERVAL_MS,
    ADV_PATH,
    APP_PATH,
    DEVICE_ID_PATH,
    MORPH_LOCAL_NAME,
    MORPH_SERVICE_PORT,
    MORPH_SERVICE_TYPE,
    NETWORK_STATUS_CHAR_PATH,
    NETWORK_STATUS_CHAR_UUID,
    SERVICE_UUID,
    SERVICE_PATH,
    WIFI_CHAR_UUID,
    WIFI_CHAR_PATH,
    WIFI_INTERFACE,
)
from constants import (
    BLUEZ_SERVICE,
    DBUS_PROPERTIES_IFACE,
    GATT_CHARACTERISTIC_IFACE,
    GATT_MANAGER_IFACE,
    GATT_SERVICE_IFACE,
    LE_ADVERTISEMENT_IFACE,
    LE_ADV_MANAGER_IFACE,
    NM_IFACE,
    NM_PATH,
    NM_SERVICE,
    OBJ_MANAGER_IFACE,
)

# Global network state counter
network_state_counter = 0

# avahi-publish process handle
avahi_proc: asyncio.subprocess.Process | None = None

async def get_ssid() -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            "sudo",
            "iw",
            "dev",
            WIFI_INTERFACE,
            "link",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode()
        return next(
            (
                line.split("SSID:", 1)[1].strip()
                for line in output.splitlines()
                if "SSID:" in line
            ),
            "",
        )
    except Exception as e:
        print("ERROR [get_ssid]:", e)
        return ""


async def get_private_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("10.255.255.255", 1))
            return sock.getsockname()[0]
    except Exception:
        pass

    proc = await asyncio.create_subprocess_shell(
        "hostname -I | awk '{print $1}'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        out, err = await proc.communicate()
        if proc.returncode == 0:
            return out.decode().strip()

        print("ERROR [get_private_ip]:", err.decode())
        return ""
    except asyncio.CancelledError:
        proc.terminate()
        await proc.wait()
        raise


async def _get_current_network_details() -> tuple[str, str]:
    return await get_ssid(), await get_private_ip()


async def _restart_avahi(device_id: str) -> None:
    """Kill any running avahi-publish and start a fresh one if WiFi is up."""
    global avahi_proc

    # Kill the existing process
    if avahi_proc is not None and avahi_proc.returncode is None:
        try:
            avahi_proc.terminate()
            await avahi_proc.wait()
        except Exception as e:
            print(f"Error stopping avahi-publish: {e}")
    avahi_proc = None

    connected = bool(await get_ssid())

    if not connected:
        print("avahi-publish: no active WiFi — not starting", flush=True)
        return

    hostname = socket.gethostname()
    service_name = f"MORPH-{hostname}"
    txt = f"DEVICE_ID={device_id}" if device_id else ""
    cmd = ["avahi-publish", "-s", service_name, MORPH_SERVICE_TYPE, MORPH_SERVICE_PORT]
    if txt:
        cmd.append(txt)
    print(f"Starting avahi-publish: {' '.join(cmd)}", flush=True)
    avahi_proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )


async def _apply_wifi(ssid: str, psk: str) -> None:
    """Rescan, delete any existing profile, then connect."""
    # Trigger a fresh scan so nmcli doesn't fail with "No network with SSID found"
    # when its cache is stale (e.g. device just powered on or moved networks).
    print(f"Rescanning WiFi before connecting to '{ssid}'...", flush=True)
    rescan_proc = await asyncio.create_subprocess_exec(
        "nmcli",
        "device",
        "wifi",
        "rescan",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await rescan_proc.wait()
    # Give the adapter a moment to populate scan results
    await asyncio.sleep(3)

    delete_proc = await asyncio.create_subprocess_exec(
        "nmcli",
        "connection",
        "delete",
        ssid,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await delete_proc.wait()
    proc = await asyncio.create_subprocess_exec(
        "nmcli",
        "device",
        "wifi",
        "connect",
        ssid,
        "password",
        psk,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode == 0:
        print(f"Successfully connected to WiFi network '{ssid}'")
    else:
        print(f"Failed to connect to WiFi network '{ssid}': {stderr.decode()}")


class Application(ServiceInterface):
    def __init__(self) -> None:
        super().__init__(OBJ_MANAGER_IFACE)

    @method()
    def GetManagedObjects(self) -> "a{oa{sa{sv}}}":
        return {
            SERVICE_PATH: {
                GATT_SERVICE_IFACE: {
                    "UUID": Variant("s", SERVICE_UUID),
                    "Primary": Variant("b", True),
                    "Includes": Variant("ao", []),
                }
            },
            WIFI_CHAR_PATH: {
                GATT_CHARACTERISTIC_IFACE: {
                    "Service": Variant("o", SERVICE_PATH),
                    "UUID": Variant("s", WIFI_CHAR_UUID),
                    "Flags": Variant("as", ["write"]),
                }
            },
            NETWORK_STATUS_CHAR_PATH: {
                GATT_CHARACTERISTIC_IFACE: {
                    "Service": Variant("o", SERVICE_PATH),
                    "UUID": Variant("s", NETWORK_STATUS_CHAR_UUID),
                    "Flags": Variant("as", ["read"]),
                }
            },
        }


class GattService(ServiceInterface):
    def __init__(self) -> None:
        super().__init__(GATT_SERVICE_IFACE)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return SERVICE_UUID

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":
        return True

    @dbus_property(access=PropertyAccess.READ)
    def Includes(self) -> "ao":
        return []


class Advertisement(ServiceInterface):
    def __init__(self, device_id: str) -> None:
        super().__init__(LE_ADVERTISEMENT_IFACE)
        self.device_id = device_id

    def increment_network_state(self) -> None:
        global network_state_counter
        network_state_counter += 1

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> "s":
        return "peripheral"

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> "as":
        return [SERVICE_UUID]

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> "s":
        return MORPH_LOCAL_NAME

    @dbus_property(access=PropertyAccess.READ)
    def ManufacturerData(self) -> "a{qv}":
        payload_bytes = f"ID={self.device_id},ST={network_state_counter}".encode(
            "utf-8"
        )
        return {0xFFFF: Variant("ay", payload_bytes)}

    @dbus_property(access=PropertyAccess.READ)
    def Includes(self) -> "as":
        return ["tx-power"]

    @dbus_property(access=PropertyAccess.READ)
    def MinInterval(self) -> "u":
        return ADV_MIN_INTERVAL_MS

    @dbus_property(access=PropertyAccess.READ)
    def MaxInterval(self) -> "u":
        return ADV_MAX_INTERVAL_MS

    @method()
    def Release(self) -> None:
        return None


def read_device_id() -> str:
    try:
        return DEVICE_ID_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


async def find_adapter_path(bus: MessageBus) -> str:
    intro = await bus.introspect(BLUEZ_SERVICE, "/")
    obj = bus.get_proxy_object(BLUEZ_SERVICE, "/", intro)
    manager = obj.get_interface(OBJ_MANAGER_IFACE)
    managed: dict[str, dict[str, Any]] = await manager.call_get_managed_objects()
    for path, ifaces in managed.items():
        if GATT_MANAGER_IFACE in ifaces and LE_ADV_MANAGER_IFACE in ifaces:
            return path
    raise RuntimeError("No BLE adapter with GATT + LE advertising manager found")


async def main() -> None:
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    adapter_path = await find_adapter_path(bus)
    device_id = read_device_id()

    app = Application()
    svc = GattService()
    wifi_ch = WifiProvisioningCharacteristic(_apply_wifi)
    adv = Advertisement(device_id)
    network_status_ch = NetworkStatusCharacteristic(
        _get_current_network_details, lambda: network_state_counter
    )

    # Fetch initial wifi state
    print("Fetching initial WiFi state...", flush=True)
    await network_status_ch.update_cached_value()
    await _restart_avahi(device_id)

    bus.export(APP_PATH, app)
    bus.export(SERVICE_PATH, svc)
    bus.export(WIFI_CHAR_PATH, wifi_ch)
    bus.export(ADV_PATH, adv)
    bus.export(NETWORK_STATUS_CHAR_PATH, network_status_ch)

    adapter_intro = await bus.introspect(BLUEZ_SERVICE, adapter_path)
    adapter_obj = bus.get_proxy_object(BLUEZ_SERVICE, adapter_path, adapter_intro)
    gatt_mgr = adapter_obj.get_interface(GATT_MANAGER_IFACE)
    adv_mgr = adapter_obj.get_interface(LE_ADV_MANAGER_IFACE)

    # Listen for network changes
    nm_intro = await bus.introspect(NM_SERVICE, NM_PATH)
    nm_obj = bus.get_proxy_object(NM_SERVICE, NM_PATH, nm_intro)
    props_iface = nm_obj.get_interface(DBUS_PROPERTIES_IFACE)

    def on_network_state_changed(
        interface_name: str, changed_properties: dict, invalidated_properties: list
    ) -> None:
        if interface_name == NM_IFACE:
            if "State" in changed_properties:
                new_state = changed_properties["State"].value
                print(f"NetworkManager State changed to: {new_state}", flush=True)

                async def sync_network_state():
                    global network_state_counter
                    network_state_counter += 1
                    await network_status_ch.update_cached_value()
                    await _restart_avahi(device_id)
                    if "PrimaryConnection" in changed_properties:
                        adv.emit_properties_changed(
                            {"ManufacturerData": adv.ManufacturerData}
                        )

                # 70 = CONNECTED_GLOBAL (IP assigned), 20 = DISCONNECTED, 30 = DISCONNECTING
                if new_state in (70, 20, 30):
                    asyncio.create_task(sync_network_state())

    props_iface.on_properties_changed(on_network_state_changed)

    await gatt_mgr.call_register_application(APP_PATH, {})
    await adv_mgr.call_register_advertisement(ADV_PATH, {})
    print(f"Advertising GATT service UUID: {SERVICE_UUID} on {adapter_path}")
    if device_id:
        print(f"Advertising DEVICE_ID from {DEVICE_ID_PATH}: {device_id}")
    else:
        print(f"No DEVICE_ID loaded from {DEVICE_ID_PATH}; advertising empty value.")
    print("Press Ctrl+C to stop.")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_event.set)
    loop.add_signal_handler(signal.SIGTERM, stop_event.set)
    await stop_event.wait()

    # Stop avahi-publish on shutdown
    if avahi_proc is not None and avahi_proc.returncode is None:
        avahi_proc.terminate()
        await avahi_proc.wait()

    await adv_mgr.call_unregister_advertisement(ADV_PATH)
    await gatt_mgr.call_unregister_application(APP_PATH)
    bus.unexport(ADV_PATH)
    bus.unexport(WIFI_CHAR_PATH)
    bus.unexport(NETWORK_STATUS_CHAR_PATH)
    bus.unexport(SERVICE_PATH)
    bus.unexport(APP_PATH)
    bus.disconnect()
    print("Advertising stopped.")


if __name__ == "__main__":
    asyncio.run(main())
