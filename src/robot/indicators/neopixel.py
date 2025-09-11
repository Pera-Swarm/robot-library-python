"""NeoPixel indicator controller mirroring Java logic."""

from __future__ import annotations

import json
from robot.mqtt.robot_mqtt_client import RobotMqttClient
from robot.mqtt.mqtt_msg import MqttMsg
from robot.types import RGBColorType
from .abstract_indicator import AbstractIndicator


class NeoPixel(AbstractIndicator):
    def __init__(self, robot, mqtt_client: RobotMqttClient):
        super().__init__(robot, mqtt_client)
        self._topics_sub: dict[str, str] = {}
        self._subscribe("NEOPIXEL_IN", f"output/neopixel/{self.robot_id}")

        # Set the default color at beginning
        self.change_color(66, 66, 66)

    def _subscribe(self, key: str, topic: str) -> None:
        self._topics_sub[key] = topic
        self.robot_mqtt_client.subscribe(topic)

    def handle_subscription(self, r, m: MqttMsg) -> None:
        topic, msg = m.topic, m.message
        if topic == self._topics_sub.get("NEOPIXEL_IN"):
            colors = msg.split(" ")
            R = int(colors[0])
            G = int(colors[1])
            B = int(colors[2])
            self.change_color(R, G, B)
        else:
            print(f"Received (unknown): {topic}> {msg}")

    def change_color(self, red: int, green: int, blue: int) -> None:
        color = RGBColorType(red, green, blue)
        obj = {"id": self.robot_id, "R": color.get_r(), "G": color.get_g(), "B": color.get_b()}
        self.robot_mqtt_client.publish("output/neopixel", json.dumps(obj))
