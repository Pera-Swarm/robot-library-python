# Robot emulator base class
# This file holds core framework for robot emulation
# RobotState - define robot state
# Motion - send move/ rotate command over mqtt
# Virtual Robot - base class for robot emulation

import time
import threading
import paho.mqtt.client as mqtt

class RobotState:
    """Define robot states"""

    BEGIN = "BEGIN"
    RUN = "RUN"
    WAIT ="WAIT"

class Motion:
    """Handle movement"""
    def __init__(self,mqtt_client,robot_id):
        self.client = mqtt_client
        self.robot_id = robot_id

    def move_distance(self, speed, distance):
        """Move forward a fixed distance"""
        self.client.publish(f"robots/{self.robot_id}/motion", f"MOVE {speed} {distance}")

    def rotate_degree(self, speed, angle):
        """Rotate by an angle"""
        self.client.publish(f"robots/{self.robot_id}/motion", f"ROTATE {speed} {angle}")

    def stop(self):
        """Stop movement"""
        self.client.publish(f"robots/{self.robot_id}/motion", "STOP")

    def move(self, left_speed, right_speed, duration):
        """Move with differential speeds for a duration"""
        self.client.publish(f"robots/{self.robot_id}/motion", f"DRIVE {left_speed} {right_speed} {duration}")

class VirtualRobot(threading.Thread):
    """Base class for virtual robot emulation"""
    """
    Extend this class and implement 'setup()' and 'loop()'
    """

    def __init__(self, robot_id, x=0, y=0, heading=0, mqtt_config = None):
        super().__init__()
        self.robot_id = robot_id
        self.x = x
        self.y = y
        self.heading = heading
        self.state = RobotState.BEGIN
        self.client = mqtt.Client()
        self.motion = Motion(self.client, self.robot_id)

        #configure mqtt
        if mqtt_config:
            self.client.username_pw_set(
                mqtt_config.get("username"),
                mqtt_config.get("password")
            )
            self.client.connect(
                mqtt_config.get("server","127.0.0.1"),
                mqtt_config.get("port",1883),
                mqtt_config.get("keepalive",60)
            )

            def setup(self):
                """Run once when the robot starts"""
                print(f"Robot {self.robot_id} setup complete")
                self.state = RobotState.RUN

            def loop(self):
                """Main loop, override this method"""
                print(f"Robot {self.robot_id} running at position ({self.x}, {self.y}) heading {self.heading}")
                pass

            def run(self):
                """Mian execution loop"""
                self.setup()
                while True:
                    try:
                        self.loop()
                        time.sleep(0.1)  # Small delay to prevent CPU overload

                    except Exception as e:
                        print(f"Error in robot {self.robot_id}: {e}")
                        break