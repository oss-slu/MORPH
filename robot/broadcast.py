import random
import socket
import time
from uuid import uuid4

from zeroconf import ServiceInfo, Zeroconf
import zeroconf

with open("wordlist.txt", "r") as f:
    words = [line.strip() for line in f.readlines()]

robot_name = "MORPH-" + "-".join(random.sample(words, 3))
service_type = "_robot._tcp.local."
local_ip = socket.gethostbyname(socket.gethostname())
port = 8080

info = ServiceInfo(
    type_=service_type,
    name=f"{robot_name}.{service_type}",
    addresses=[socket.inet_aton(local_ip)],
    port=port,
    properties={},
    server=f"{robot_name}.local.",
)

zeroconf = Zeroconf()
zeroconf.register_service(info)

try:
    while True:
        time.sleep(1)
finally:
    zeroconf.unregister_service(info)
    zeroconf.close()
