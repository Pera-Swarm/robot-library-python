from __future__ import annotations

import types

import pytest

from robot.mqtt.robot_mqtt_client import RobotMqttClient


class FakeClient:
    """Minimal stand-in for paho.mqtt.client.Client."""

    def __init__(self):
        self.published = []
        self.subscribed = []
        self.loop_started = False
        self.loop_stopped = False
        self.disconnected = False
        self.reconnected = False
        self.creds = None
        # Callbacks are set by RobotMqttClient after construction.
        self.on_connect = None
        self.on_message = None
        self.on_disconnect = None

    def username_pw_set(self, username: str, password: str) -> None:  # pragma: no cover - simple setter
        self.creds = (username, password)

    def connect(self, server: str, port: int, keepalive: int) -> None:  # pragma: no cover - simple setter
        self.connected_args = (server, port, keepalive)

    def reconnect(self) -> None:
        self.reconnected = True

    def loop_start(self) -> None:
        self.loop_started = True

    def loop_stop(self) -> None:
        self.loop_stopped = True

    def disconnect(self) -> None:
        self.disconnected = True

    def publish(self, topic: str, body: str, qos: int = 0, retain: bool = False) -> None:
        self.published.append((topic, body, qos, retain))

    def subscribe(self, topic: str) -> None:
        self.subscribed.append(topic)


@pytest.fixture(autouse=True)
def patch_mqtt_client(monkeypatch):
    """Replace paho.mqtt with a lightweight fake and skip real sleeps."""
    import robot.mqtt.robot_mqtt_client as mqtt_client_mod

    monkeypatch.setattr(
        mqtt_client_mod,
        "mqtt",
        types.SimpleNamespace(Client=FakeClient),
    )
    monkeypatch.setattr(mqtt_client_mod.time, "sleep", lambda *_args, **_kwargs: None)
    yield


def test_publish_prefix():
    client = RobotMqttClient("srv", 1883, None, None, "chan")
    fake = client._client  # type: ignore[attr-defined]

    client.publish("foo", "bar")

    assert fake.published[0][0] == "chan/foo"
    assert fake.published[0][1] == "bar"


def test_subscribe_prefix():
    client = RobotMqttClient("srv", 1883, None, None, "chan")
    fake = client._client  # type: ignore[attr-defined]

    client.subscribe("abc")

    assert fake.subscribed[0] == "chan/abc"


def test_on_message_strips_channel_and_enqueues():
    client = RobotMqttClient("srv", 1883, None, None, "chan")

    msg = types.SimpleNamespace(topic="chan/robot/msg/10", payload=b"START")
    client._on_message(None, None, msg)  # noqa: SLF001

    m = client.in_queue_pop()
    assert m is not None
    assert m.topic == "robot/msg/10"
    assert m.message == "START"


def test_disconnect_attempts_reconnect():
    client = RobotMqttClient("srv", 1883, None, None, "chan")
    fake = client._client  # type: ignore[attr-defined]

    client._on_disconnect(None, None, 0)  # noqa: SLF001

    assert fake.reconnected is True


def test_close_stops_loop_and_disconnects():
    client = RobotMqttClient("srv", 1883, None, None, "chan")
    fake = client._client  # type: ignore[attr-defined]

    client.close()

    assert fake.loop_stopped is True
    assert fake.disconnected is True
