from __future__ import annotations

from robot.interfaces import IMqttHandler
from robot.mqtt.robot_mqtt_client import RobotMqttClient


class AbstractSensor(IMqttHandler):
    def __init__(self, robot, mqtt_client: RobotMqttClient):
        self.robot_mqtt_client = mqtt_client
        self.robot_id = robot.get_id()
        self.robot = robot

    def handle_subscription(self, r, m):  # default no-op
        pass
