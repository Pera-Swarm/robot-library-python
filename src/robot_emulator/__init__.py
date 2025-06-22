"""
Robot Emulator

A python package to emulate robot behaviour

Virtual Robot - Java Implementation - https://pera-swarm.ce.pdn.ac.lk/docs/robots/virtual/v1/java/

"""

import configparser
import threading
import os

from configs.mqtt_settings import MQTTSettings
from robots.my_test_robot import MyTestRobot

def load_mqtt_config(path="resources/config/mqtt.properties"):
    if not os.path.exists(path):
        print("Config file, `resources/config/mqtt.properties` Not Found !!!")
        return False

    config = configparser.ConfigParser()
    with open(path, 'r') as f:
        config.read_file(f)

    # Java .properties files don't use sections, so we fake one
    mqtt_config = config['DEFAULT']

    MQTTSettings.server = mqtt_config.get("server", "")
    MQTTSettings.port = int(mqtt_config.get("port", "1883"))
    MQTTSettings.userName = mqtt_config.get("username", "")
    MQTTSettings.password = mqtt_config.get("password", "")
    MQTTSettings.channel = mqtt_config.get("channel", "v1")

    return True

def main():
    if not load_mqtt_config():
        return

    # Start a single robot
    robot = MyTestRobot(10, 0, 0, 90)
    robot_thread = threading.Thread(target=robot.run)  # assuming robot has run()
    robot_thread.start()

    # Optional: Start a swarm of robots
    # robot_ids = list(range(10))
    # robots = []
    # for i in robot_ids:
    #     r = MyTestRobot(i, 40 * i, 50 * i, 90 + 10 * i)
    #     t = threading.Thread(target=r.run)
    #     t.start()
    #     robots.append((r, t))

if __name__ == "__main__":
    main()

