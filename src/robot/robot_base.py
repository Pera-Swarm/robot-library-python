"""
Base Robot class.
"""

import time
import threading
from robot.mqtt_client import RobotMqttClient
from robot.helpers.coordinate import Coordinate
from robot.helpers.robot_mqtt import RobotMQTT 

class Robot:
    """
    Base robot class providing lifecycle management.
    - Initializes MQTT client, coordinate tracker, and RobotMQTT helper
    - Provides setup() for sensors and communication helpers
    - Provides a run loop that calls user-defined loop() at fixed intervals
      while dispatching inbound MQTT messages
    """

    def __init__(self, robot_id: str,
                 broker_host="127.0.0.1", broker_port=1883,
                 username=None, password=None,
                 loop_hz=10):
        """
        Initialize base robot.
        :param robot_id: Unique robot identifier
        :param broker_host: MQTT broker host
        :param broker_port: MQTT broker port
        :param username: optional username
        :param password: optional password
        :param loop_hz: Frequency of the run loop (Hz)
        """
        self.robot_id = robot_id
        self.loop_hz = loop_hz
        self._stop_event = threading.Event()

        # Core components
        self.coordinate = Coordinate()
        self.mqtt_client = RobotMqttClient(
            client_id=robot_id,
            server=broker_host,
            port=broker_port,
            username=username,
            password=password
        )
        self.robot_mqtt = RobotMQTT(robot_id, self.mqtt_client, self.coordinate)

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def setup(self):
        """
        Setup hook for initializing sensors, communication helpers, and outputs.
        Override in subclass.
        """
        pass

    def loop(self):
        """
        Main robot behavior loop.
        Override in subclass to implement robot logic.
        """
        pass

    def run(self):
        """
        Run the robot main loop:
          - Connects MQTT client
          - Calls setup()
          - Executes loop() at fixed interval
          - Dispatches inbound messages
        """
        print(f"[Robot] Starting {self.robot_id}")

        # Connect MQTT
        self.mqtt_client.set_message_callback(self._on_message)
        self.mqtt_client.connect()

        # Call user setup
        self.setup()

        interval = 1.0 / self.loop_hz
        try:
            while not self._stop_event.is_set():
                start = time.time()

                # Dispatch inbound MQTT messages
                self._dispatch_inbound()

                # Run user loop
                self.loop()

                # Sleep to maintain loop frequency
                elapsed = time.time() - start
                time.sleep(max(0, interval - elapsed))
        except KeyboardInterrupt:
            print(f"[Robot] Stopping {self.robot_id}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of robot and MQTT client."""
        print("[Robot] Shutting down...")
        self._stop_event.set()
        self.mqtt_client.disconnect()

    # ---------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------

    def _dispatch_inbound(self):
        """Drain inbound MQTT messages and forward to RobotMQTT handler."""
        while not self.mqtt_client.inbound_queue.empty():
            topic, payload = self.mqtt_client.inbound_queue.get()
            self.robot_mqtt.handle_incoming(topic, payload)

    def _on_message(self, topic, payload):
        """Callback from MQTT client, just enqueues messages."""
        self.mqtt_client.inbound_queue.put((topic, payload))
