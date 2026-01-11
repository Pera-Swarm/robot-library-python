from __future__ import annotations

from collections import deque
import time
from typing import Deque

import paho.mqtt.client as mqtt

from robot.exception import MqttClientException
from robot.mqtt.mqtt_msg import MqttMsg


class RobotMqttClient:
    """MQTT client wrapper mirroring Java's RobotMqttClient.

    - Maintains `in_queue` and `out_queue` of `MqttMsg`.
    - Prefixes publish/subscribe topics with `MQTTSettings.channel` externally.
    """

    def __init__(
        self,
        server: str,
        port: int,
        user_name: str | None,
        password: str | None,
        channel: str,
    ):
        self.server = server
        self.port = int(port)
        self.user_name = user_name or ""
        self.password = password or ""
        self.channel = channel or ""

        self._client = mqtt.Client()
        self._connected = False

        # Incoming/outgoing queues
        self.in_queue: Deque[MqttMsg] = deque()
        self.out_queue: Deque[MqttMsg] = deque()

        # Setup callbacks
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        self._connect()

    # Connection management -------------------------------------------------
    def _connect(self) -> None:
        try:
            if self.user_name:
                self._client.username_pw_set(self.user_name, self.password)
            # Start network loop in a background thread
            self._client.connect(self.server, self.port, keepalive=60)
            self._client.loop_start()
            self._connected = True
            print("MQTT: Connected")
        except Exception as e:
            # broad but acceptable for connection bootstrapping
            print(f"MQTT connection error: {e}")
            self._connected = False
            raise MqttClientException(f"MQTT connection error: {e}")

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc):  # noqa: ANN001, ANN201
        if rc == 0:
            self._connected = True
        else:
            print(f"MQTT: Connection failed with code {rc}")

    def _on_disconnect(self, client: mqtt.Client, userdata, rc):  # noqa: ANN001, ANN201
        self._connected = False
        print("Connection lost!")
        # Lightweight auto-reconnect attempt; avoid tight loop on persistent failure.
        time.sleep(1)
        try:
            # loop_start is already running; just reconnect the socket
            self._client.reconnect()
        except Exception as e:
            print(f"MQTT reconnect failed: {e}")

    # MQTT callbacks --------------------------------------------------------
    def _on_message(
        self,
        client: mqtt.Client,
        userdata,
        msg: mqtt.MQTTMessage,
    ):  # noqa: ANN001, ANN201
        topic = getattr(msg, "topic", "") or ""
        raw_payload = getattr(msg, "payload", b"")
        try:
            payload = raw_payload.decode("utf-8") if isinstance(raw_payload, (bytes, bytearray)) else str(raw_payload)
        except Exception:
            payload = str(raw_payload)

        if not topic or not payload:
            return

        # Strip channel prefix before enqueueing, matching Java behavior
        if "/" in topic:
            t = topic[topic.find("/") + 1 :]
        else:
            t = topic

        self.in_queue.append(MqttMsg(t, payload))


    # API -------------------------------------------------------------------
    def publish(
        self, topic: str, body: str, qos: int = 0, retained: bool = False
    ) -> None:
        if not (self._connected and topic and body):
            raise MqttClientException("Not Connected or empty topic/body")
        full_topic = f"{self.channel}/{topic}" if self.channel else topic
        try:
            self._client.publish(full_topic, body, qos=qos, retain=retained)
        except Exception as e:
            raise MqttClientException(str(e))

    def subscribe(self, topic: str) -> None:
        if not (self._connected and topic):
            raise MqttClientException("Not Connected or empty topic")
        full_topic = f"{self.channel}/{topic}" if self.channel else topic
        try:
            self._client.subscribe(full_topic)
            print(f"Subscribed to {full_topic}")
        except Exception as e:
            raise MqttClientException(str(e))

    def in_queue_pop(self) -> MqttMsg | None:
        return self.in_queue.popleft() if self.in_queue else None

    def out_queue_pop(self) -> MqttMsg | None:
        return self.out_queue.popleft() if self.out_queue else None

    def close(self) -> None:
        """Stop the network loop and disconnect cleanly."""
        try:
            self._client.loop_stop()
            self._client.disconnect()
        finally:
            self._connected = False