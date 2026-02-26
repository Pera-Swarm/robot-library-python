"""Proximity sensor implementation mirroring Java logic."""

from __future__ import annotations

import json
from time import time

from robot.exception import SensorException
from robot.mqtt.mqtt_msg import MqttMsg
from robot.mqtt.robot_mqtt_client import RobotMqttClient
from robot.types import ProximityReadingType

from .abstract_sensor import AbstractSensor


class ProximitySensor(AbstractSensor):
    MQTT_TIMEOUT = 2000  # ms

    def __init__(self, robot, mqtt_client: RobotMqttClient):
        super().__init__(robot, mqtt_client)
        self._topics_sub: dict[str, str] = {}
        self._subscribe("PROXIMITY_IN", f"sensor/proximity/{self.robot_id}")
        self._proximity_lock = False
        self._proximity: ProximityReadingType | None = None
        self._angles: list[int] = [0]

    def __init__with_angles(
        self, robot, angles: list[int], mqtt_client: RobotMqttClient
    ):  # helper to mirror overload
        super().__init__(robot, mqtt_client)
        self._topics_sub = {}
        self._angles = list(angles)
        self._subscribe("PROXIMITY_IN", f"sensor/proximity/{self.robot_id}")
        self._proximity_lock = False
        self._proximity = None

    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def handle_subscription(self, robot, m: MqttMsg) -> None:
        topic, msg = m.topic, m.message
        if topic == self._topics_sub.get("PROXIMITY_IN"):
            try:
                self._proximity = ProximityReadingType(self._angles, msg)
            except Exception as e:  # noqa: BLE001
                print(e)
            self._proximity_lock = False
        else:
            print(f"Received (unknown): {topic}> {msg}")

    def set_angles(self, proximity_angles: list[int]) -> None:
        self._angles = list(proximity_angles)

    def get_proximity(self) -> ProximityReadingType:
        angle_array = list(self._angles)
        msg = {"id": self.robot_id, "angles": angle_array, "reality": "V"}
        self._proximity_lock = True
        self.robot_mqtt_client.publish("sensor/proximity", json.dumps(msg))
        self.robot.delay(250 * len(self._angles))

        start_time = time() * 1000
        timeout = False
        while self._proximity_lock and not timeout:
            try:
                self.robot.handle_subscribe_queue()
            except Exception as e:  # noqa: BLE001
                print(e)
            self.robot.delay(100)
            timeout = time() * 1000 - start_time > self.MQTT_TIMEOUT

        if timeout:
            raise SensorException("Proximity sensor timeout")
        assert self._proximity is not None
        return self._proximity

    def send_proximity(self) -> None:
        assert self._proximity is not None
        obj = {"id": self.robot_id, "proximity": str(self._proximity)}
        self.robot_mqtt_client.publish("sensor/proximity/", json.dumps(obj))
