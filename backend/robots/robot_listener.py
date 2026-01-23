from logging import info
from math import inf
from sqlite3 import adapt
from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
import socket

from robots.robot import Robot


class RobotListener(ServiceListener):
    def __init__(self):
        self.robots: dict[str, Robot] = {}

    def _service_name_to_robot_name(self, service_name: str) -> str:
        print("UPDATED", service_name)
        return service_name.split("._")[0]

    def _update_robot(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            address = (
                info.parsed_addresses()[0] if info.parsed_addresses() else "Unknown"
            )
            robot_name = self._service_name_to_robot_name(name)
            self.robots[name] = Robot(
                host=address,
                port=int(info.port),
                name=robot_name,
                properties=info.properties,
            )

    def _delete_robot(self, name: str) -> None:
        if name in self.robots:
            del self.robots[name]

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._update_robot(zc, type_, name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._update_robot(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._delete_robot(name)
