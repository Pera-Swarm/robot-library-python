from __future__ import annotations

from robot.mqtt.robot_mqtt_client import RobotMqttClient


class AbstractIndicator:
    def __init__(self, robot, mqtt_client: RobotMqttClient):
        self.robot_mqtt_client = mqtt_client
        self.robot_id = robot.get_id()
        self.robot = robot

    def handle_subscription(self, r, m):  # must be overridden in subclasses
        raise NotImplementedError
