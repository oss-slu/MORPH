from dataclasses import dataclass


@dataclass
class Robot:
    host: str
    port: int
    name: str
    properties: dict
