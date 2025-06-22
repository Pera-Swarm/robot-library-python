"""
Configuration class for the robot_emulator package.

"""

import configparser
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".robot_emulator" / "config.ini"

class Config:
    def __init__(self, broker: str, port: int, robot_id: str, topic_prefix: str = "swarm"):
        self.broker = broker
        self.port = port
        self.robot_id = robot_id
        self.topic_prefix = topic_prefix

    def __repr__(self):
        return f"<Config broker={self.broker}, port={self.port}, robot_id={self.robot_id}>"

def load_config(config_path: str = None) -> Config:
    config = configparser.ConfigParser()

    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    config.read(path)

    try:
        broker = config.get("MQTT", "broker")
        port = config.getint("MQTT", "port")
        robot_id = config.get("Robot", "robot_id")
        topic_prefix = config.get("MQTT", "topic_prefix", fallback="swarm")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        raise ValueError(f"Invalid config file structure: {e}")

    return Config(broker=broker, port=port, robot_id=robot_id, topic_prefix=topic_prefix)
