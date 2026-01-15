"""Distance sensor implementation mirroring Java logic."""

from __future__ import annotations

import json
from time import time

from robot.mqtt.robot_mqtt_client import RobotMqttClient
from robot.mqtt.mqtt_msg import MqttMsg
from robot.exception import SensorException
from .abstract_sensor import AbstractSensor


class DistanceSensor(AbstractSensor):
    MQTT_TIMEOUT = 1000  # ms

    def __init__(self, robot, mqtt_client: RobotMqttClient):
        super().__init__(robot, mqtt_client)
        self._topics_sub: dict[str, str] = {}
        self._subscribe("DISTANCE_IN", f"sensor/distance/{self.robot_id}")
        self._subscribe("DISTANCE_LOOK", f"sensor/distance/{self.robot_id}/?")
        self._dist_lock = False
        self._dist_value = 0

    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def handle_subscription(self, robot, m: MqttMsg) -> None:
        topic, msg = m.topic, m.message
        if topic == self._topics_sub.get("DISTANCE_IN"):
            if msg == "Infinity":
                self._dist_value = -1
            else:
                self._dist_value = int(msg)
            self._dist_lock = False
        else:
            print(f"Received (unknown): {topic}> {msg}")

    def get_distance(self) -> float:
        msg = {"id": self.robot_id, "reality": "M"}
        self._dist_lock = True
        self.robot_mqtt_client.publish("sensor/distance", json.dumps(msg))
        self.robot.delay(250)

        start_time = time() * 1000
        timeout = False
        while self._dist_lock and not timeout:
            try:
                self.robot.handle_subscribe_queue()
            except Exception as e:  # noqa: BLE001
                print(e)
            self.robot.delay(100)
            timeout = (time() * 1000 - start_time > self.MQTT_TIMEOUT)

        if timeout:
            raise SensorException("Distance sensor timeout")

        return float(self._dist_value)

    def send_distance(self, dist: float) -> None:
        obj = {"id": self.robot_id, "dist": dist}
        # Align with request topic used in get_distance()
        self.robot_mqtt_client.publish("sensor/distance", json.dumps(obj))
