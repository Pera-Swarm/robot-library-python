"""Color sensor implementation mirroring Java logic."""

from __future__ import annotations

import json
from time import time

from robot.exception import SensorException
from robot.mqtt.mqtt_msg import MqttMsg
from robot.mqtt.robot_mqtt_client import RobotMqttClient
from robot.types import RGBColorType

from .abstract_sensor import AbstractSensor


class ColorSensor(AbstractSensor):
    MQTT_TIMEOUT = 1000  # ms

    def __init__(self, robot, mqtt_client: RobotMqttClient):
        super().__init__(robot, mqtt_client)
        self._topics_sub: dict[str, str] = {}
        self.color = RGBColorType(0, 0, 0)
        self._subscribe("COLOR_IN", f"sensor/color/{self.robot_id}")
        self._subscribe("COLOR_LOOK", f"sensor/color/{self.robot_id}/?")
        self._col_lock = False

    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def handle_subscription(self, robot, m: MqttMsg) -> None:
        topic, msg = m.topic, m.message
        if topic == self._topics_sub.get("COLOR_IN"):
            self.color.set_color_from_str(msg)
            self._col_lock = False
        else:
            print(f"Received (unknown): {topic}> {self.color}")

    def get_color(self) -> RGBColorType:
        msg = {"id": self.robot_id, "reality": "M"}
        self._col_lock = True
        self.robot_mqtt_client.publish("sensor/color", json.dumps(msg))
        self.robot.delay(250)

        start_time = time() * 1000
        timeout = False
        while self._col_lock and not timeout:
            try:
                self.robot.handle_subscribe_queue()
            except Exception as e:  # noqa: BLE001
                print(e)
            self.robot.delay(100)
            timeout = time() * 1000 - start_time > self.MQTT_TIMEOUT

        if timeout:
            raise SensorException("Color sensor timeout")
        return self.color

    def send_color(self, red: int, green: int, blue: int, ambient: int) -> None:
        obj = {
            "id": self.robot_id,
            "R": red,
            "G": green,
            "B": blue,
            "ambient": ambient,
        }
        self.robot_mqtt_client.publish("sensor/color/", json.dumps(obj))
