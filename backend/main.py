from contextlib import asynccontextmanager
from pydoc import cli
from fastapi import FastAPI, WebSocket
from fastapi.logger import logger
from pydantic import BaseModel
from zeroconf import ServiceBrowser, Zeroconf
import socketio
import asyncio

from robots.robot import Robot
from robots.robot_listener import RobotListener
from foxglove.client import FoxgloveClient
from utils.command_converter import CommandConverter
from utils.sio_pydantic_wrapper import siomodel


zeroconf = Zeroconf()
robot_listener = RobotListener()
browser = ServiceBrowser(zeroconf, "_robot._tcp.local.", robot_listener)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
foxglove_clients: dict[str, FoxgloveClient] = {}

reserve_lock = asyncio.Lock()
sid_to_robot: dict[str, Robot] = {}
reservations: dict[str, str] = {}  # robot_name -> sid


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        zeroconf.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy"}


@app.get("/robots")
async def get_robots():
    return [
        {"name": robot.name, "host": robot.host, "port": robot.port}
        for robot in robot_listener.robots.values()
    ]


@sio.event
async def connect(sid, environ, auth):
    logger.info("Socket connected:", sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket disconnected:", sid)

    async with reserve_lock:
        robot = sid_to_robot.get(sid)
        if robot:
            del sid_to_robot[sid]
            del reservations[robot.name]


class ConnectData(BaseModel):
    robot_name: str


@sio.on("connect_robot")
@siomodel(ConnectData)
async def handle_connect_robot(sid: str, data: ConnectData) -> None:
    robot = robot_listener.robots.get(data.robot_name)
    if not robot:
        raise ConnectionRefusedError("Robot not found")

    async with reserve_lock:
        if data.robot_name in reservations and reservations[data.robot_name] != sid:
            raise ConnectionRefusedError("Robot already reserved")

        sid_to_robot[sid] = robot
        reservations[robot.name] = sid

        client = foxglove_clients.get(robot.name)
        if not client:
            client = FoxgloveClient(robot.host, robot.port, sio)
            await client.connect()
            foxglove_clients[robot.name] = client

        await client.connect()

    await sio.emit("connection", {"status": "connected"}, to=sid)


@sio.on("check_robot_status")
async def handle_check_robot_status(sid: str, data: dict) -> None:
    robot = sid_to_robot.get(sid)
    if not robot:
        await sio.disconnect(sid)
        return

    await sio.emit("robot_status", {"status": "connected"}, to=sid)


class SendData(BaseModel):
    command: str = "stop"
    speed: int = 100


@sio.on("send_command")
@siomodel(SendData)
async def handle_send_command(sid: str, data: SendData) -> None:
    robot = sid_to_robot.get(sid)
    if not robot:
        await sio.disconnect(sid)
        return

    client = foxglove_clients.get(robot.name)
    if not client:
        raise RuntimeError("Foxglove client not found")

    speed_factor = CommandConverter.speed_percentage_to_factor(data.speed)
    twist = CommandConverter.command_to_twist(data.command, speed_factor)
    await client.send_twist_command(**twist)


app = socketio.ASGIApp(sio, app)
