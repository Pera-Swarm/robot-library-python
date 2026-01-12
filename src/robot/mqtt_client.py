"""Compatibility re-export for RobotMqttClient.

The implementation lives in `robot.mqtt.robot_mqtt_client`.
"""

from .mqtt.robot_mqtt_client import RobotMqttClient

__all__ = ["RobotMqttClient"]
