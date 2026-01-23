from contextlib import asynccontextmanager
from fastapi import FastAPI
from zeroconf import ServiceBrowser, Zeroconf

from robots.robot_listener import RobotListener


zeroconf = Zeroconf()
robot_listener = RobotListener()
browser = ServiceBrowser(zeroconf, "_robot._tcp.local.", robot_listener)


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
