from __future__ import annotations

from robot.interfaces import IMqttHandler
from robot.mqtt.robot_mqtt_client import RobotMqttClient


class Communication(IMqttHandler):
    def __init__(self, robot_id: int, mqtt_client: RobotMqttClient):
        self.robot_mqtt_client = mqtt_client
        self.robot_id = robot_id

    def send_message(self, msg: str) -> None:  # abstract
        raise NotImplementedError

    def send_message_with_distance(self, msg: str, distance: int) -> None:  # abstract
        raise NotImplementedError
