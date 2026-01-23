import asyncio
import json
import struct
import traceback
from socketio import AsyncClient, AsyncServer
import websockets

from config import COMMAND_CHANNEL_ID, TOPICS_TO_SUBSCRIBE
from foxglove.constants import (
    ENCODING_CDR,
    MESSAGE_DATA_OPCODE,
    SERVER_FRAME_HEADER_LEN,
)
from foxglove.protocol import (
    advertise_twist_channel,
    build_twist_stamped_frame,
    parse_cdr_string,
)


class FoxgloveClient:
    def __init__(self, host: str, port: int, frontend_sock: AsyncServer):
        self._host = host
        self._port = port
        self._frontend_sock = frontend_sock
        self._wsclient = AsyncClient()
        self._ws = None
        self.command_channel_id = COMMAND_CHANNEL_ID
        self.subscribed_topics: dict[int, str] = {}
        self.command_channel_id = COMMAND_CHANNEL_ID
        self.topics_to_subscribe = TOPICS_TO_SUBSCRIBE
        self.channel_info: dict[int, dict[str, str]] = (
            {}
        )  # channel_id → {topic, encoding, schemaName}

    async def _emit_log(self, message: str):
        await self._frontend_sock.emit("log", message)

    async def _emit_ros_message(self, data: dict):
        await self._frontend_sock.emit("ros_message", data)

    async def connect(self):
        await self._emit_log(f"Connecting to Foxglove at {self._host}:{self._port}")
        self._ws = await websockets.connect(
            uri=f"ws://{self._host}:{self._port}",
            subprotocols=["foxglove.websocket.v1"],  # type: ignore
        )
        if self._ws is None:
            await self._emit_log("Failed to connect to Foxglove WebSocket")
            raise RuntimeError("WebSocket connection failed")

        await self._emit_log("Connected to Foxglove WebSocket")

    async def _cleanup_connection(self) -> None:
        """Clean up WebSocket connection resources."""
        self.running = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
        await self._emit_log("✗ WebSocket DISCONNECTED")

    async def _advertise_command_channel(self) -> None:
        """
        Advertise the command channel for publishing Twist messages.

        This tells the server that we will publish geometry_msgs/msg/TwistStamped
        messages on the /diff_drive_base/cmd_vel topic.
        """
        try:
            await advertise_twist_channel(
                self._ws, self.command_channel_id, "/diff_drive_base/cmd_vel"
            )
            await self._emit_log(
                f"✓ Client advertised /command (JSON Twist, channel {self.command_channel_id})"
            )
            await asyncio.sleep(0.2)  # Brief delay after advertising
        except Exception as e:
            await self._emit_log(f"✗ Error advertising command channel: {e}")  # type: ignore
            traceback.print_exc()

    async def _handle_messages(self) -> None:
        """
        Handle incoming messages from the Foxglove server.

        Processes both text (JSON control messages) and binary (ROS2 data) frames.
        Automatically subscribes to configured topics when they are advertised.
        """
        if not self.connected or self._ws is None:
            await self._emit_log("⚠️ Cannot handle messages - not connected")
            return

        try:
            async for message in self._ws:
                if not (self.running and self.connected and self._ws is not None):
                    break

                try:
                    if isinstance(message, str):
                        await self._handle_text_message(message)
                    elif isinstance(message, (bytes, bytearray)):
                        await self._handle_binary_message(bytes(message))

                except json.JSONDecodeError as e:
                    await self._emit_log(f"⚠️ JSON decode error: {e}")
                except Exception as e:
                    await self._emit_log(f"⚠️ Message processing error: {e}")
                    traceback.print_exc()

        except Exception as e:
            await self._emit_log(f"⚠️ Message handling error: {e}")
            traceback.print_exc()
            self.connected = False

    async def _handle_text_message(self, message: str) -> None:
        """
        Handle text (JSON) protocol messages from server.

        Processes control messages like 'advertise' and automatically subscribes
        to topics we're interested in.

        Args:
            message: JSON string message from server
        """
        data = json.loads(message)
        op = data.get("op")

        if op == "advertise":
            # Server is advertising available channels/topics
            channels = data.get("channels", [])
            await self._emit_log(f"📋 Server advertised {len(channels)} channel(s)")

            for channel in channels:
                topic = channel.get("topic", "unknown")
                channel_id = channel.get("id")
                encoding = channel.get("encoding", "unknown")
                schema_name = channel.get("schemaName", "")

                # Store channel information
                self.channel_info[channel_id] = {
                    "topic": topic,
                    "encoding": encoding,
                    "schemaName": schema_name,
                }
                await self._emit_log(
                    f" • {topic} (channel={channel_id}, encoding={encoding})"
                )

                # Auto-subscribe to topics we're interested in
                if topic in self.topics_to_subscribe:
                    await self.subscribe_to_channel(channel_id, topic)
        else:
            await self._emit_log(f"→ Protocol message: {data}")

    async def _handle_binary_message(self, message_bytes: bytes) -> None:
        """
        Handle binary message frames from server.

        Parses ROS2 message data from binary frames and forwards to frontend.
        Supports both JSON and CDR encodings.

        Args:
            message_bytes: Binary frame data
        """
        if len(message_bytes) < SERVER_FRAME_HEADER_LEN:
            await self._emit_log(f"⚠️ Short binary frame (len={len(message_bytes)})")
            return

        if message_bytes[0:1] != MESSAGE_DATA_OPCODE:
            await self._emit_log(
                f"⚠️ Unknown opcode {message_bytes[0]:02x} in binary frame"
            )
            return

        # Parse frame header
        channel_id = struct.unpack_from("<I", message_bytes, 1)[0]
        timestamp_ns = struct.unpack_from("<Q", message_bytes, 1 + 4)[0]
        payload = message_bytes[SERVER_FRAME_HEADER_LEN:]

        # Try to decode as JSON first
        try:
            txt = payload.decode("utf-8")
            maybe_json = json.loads(txt)
            await self._emit_ros_message(
                {
                    "channel_id": channel_id,
                    "timestamp_ns": timestamp_ns,
                    "data": maybe_json,
                }
            )
            await self._emit_log(
                f"→ [{channel_id}] JSON @ {timestamp_ns} ns: {maybe_json}"
            )
            return
        except Exception:
            pass

        # Try CDR encoding for std_msgs/msg/String
        info = self.channel_info.get(channel_id, {})
        schema = info.get("schemaName")
        encoding = info.get("encoding")

        # Skip ROS log messages to reduce noise
        if schema == "rcl_interfaces/msg/Log":
            return

        if schema == "std_msgs/msg/String" and encoding == ENCODING_CDR:
            try:
                cdr_string = parse_cdr_string(payload)
                await self._emit_ros_message(
                    {
                        "channel_id": channel_id,
                        "timestamp_ns": timestamp_ns,
                        "data": {"data": cdr_string},
                    }
                )
                await self._emit_log(
                    f"→ [{channel_id}] CDR @ {timestamp_ns} ns: {cdr_string}"
                )
            except Exception:
                await self._emit_log(
                    f"→ [{channel_id}] Unable to parse CDR String ({len(payload)}B)"
                )
        else:
            # Unknown encoding or schema
            head = payload[:32]
            await self._emit_ros_message(
                {
                    "channel_id": channel_id,
                    "timestamp_ns": timestamp_ns,
                    "data": "<non-JSON payload>",
                }
            )
            await self._emit_log(
                f"→ [{channel_id}] {schema or 'unknown'} with {encoding or 'unknown'} "
                f"encoding not decoded; first bytes: {head.hex()} …"
            )

    async def subscribe_to_channel(self, channel_id: int, topic: str) -> None:
        """
        Subscribe to a server-advertised channel.

        Args:
            channel_id: Channel ID to subscribe to
            topic: Topic name for logging
        """
        try:
            subscription_id = len(self.subscribed_topics) + 1
            subscribe_msg = {
                "op": "subscribe",
                "subscriptions": [
                    {
                        "id": subscription_id,
                        "channelId": channel_id,
                        "topic": topic,
                        "encoding": "json",
                    }
                ],
            }
            await self._ws.send(json.dumps(subscribe_msg))
            self.subscribed_topics[subscription_id] = topic
            await self._emit_log(
                f"✓ Subscribed: {topic} (subId={subscription_id}, channelId={channel_id})"
            )
        except Exception as e:
            await self._emit_log(f"⚠️ Error subscribing to {topic}: {e}")

    async def send_twist_command(
        self,
        linear_x: float = 0.0,
        linear_y: float = 0.0,
        linear_z: float = 0.0,
        angular_x: float = 0.0,
        angular_y: float = 0.0,
        angular_z: float = 0.0,
        frame_id: str = "base_link",
    ) -> None:
        """
        Send a TwistStamped command message to the robot.

        Args:
            linear_x: Linear velocity in x direction (m/s)
            linear_y: Linear velocity in y direction (m/s)
            linear_z: Linear velocity in z direction (m/s)
            angular_x: Angular velocity around x axis (rad/s)
            angular_y: Angular velocity around y axis (rad/s)
            angular_z: Angular velocity around z axis (rad/s)
            frame_id: Reference frame ID
        """
        if not (self.connected and self._ws):
            await self._emit_log("⚠️ Not connected; cannot send command")
            return

        # Build and send frame
        frame = build_twist_stamped_frame(
            self.command_channel_id,
            linear_x,
            linear_y,
            linear_z,
            angular_x,
            angular_y,
            angular_z,
            frame_id,
        )

        await self._ws.send(frame)
        await self._emit_log(
            f"→ Sent /diff_drive_base/cmd_vel (TwistStamped): "
            f"linear=({linear_x},{linear_y},{linear_z}), "
            f"angular=({angular_x},{angular_y},{angular_z})"
        )
