"""
MQTT client wrapper for robot communication.
"""

import queue
import threading
import time
import paho.mqtt.client as mqtt

class RobotMqttClient:
    """
    A wrapper around paho-mqtt that handles:
      - Connecting & reconnecting to broker
      - Publishing messages with QoS/retain
      - Subscribing to topics
      - Maintaining inbound/outbound message queues
      - Callback hooks for message arrival
    """

    def __init__(self, client_id, server="127.0.0.1", port=1883,
                 username=None, password=None, keepalive=60, autoreconnect=True):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.keepalive = keepalive
        self.autoreconnect = autoreconnect

        # Queues
        self.inbound_queue = queue.Queue() # all msgs received
        self.outbound_queue = queue.Queue() # msgs to be sent

        # Event for stopping background loop
        self._stop_event = threading.Event()

        # Create Paho client
        self.client = mqtt.Client(client_id=str(client_id), clean_session=True)

        if username and password:
            self.client.username_pw_set(username, password)

        # Attach callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish

        # User-defined callback for new messages
        self.on_message_callback = None

    # ---------------------------------------------------------
    # MQTT Lifecycle
    # ---------------------------------------------------------

    def connect(self):
        """Connect to MQTT broker and start background loop."""
        self.client.connect(self.server, self.port, self.keepalive)
        self.client.loop_start()

        # Start outbound publisher thread
        self._publisher_thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._publisher_thread.start()

    def disconnect(self):
        """Disconnect cleanly."""
        self._stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()

    # ---------------------------------------------------------
    # Publish / Subscribe
    # ---------------------------------------------------------

    def publish(self, topic, payload, qos=0, retain=False):
        """Queue a message for publishing."""
        self.outbound_queue.put((topic, payload, qos, retain))

    def subscribe(self, topic, qos=0):
        """Subscribe to a topic."""
        self.client.subscribe(topic, qos)

    def set_message_callback(self, callback):
        """
        Set a callback for when a message arrives.
        Callback should accept (topic, payload).
        """
        self.on_message_callback = callback

    # ---------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------

    def _publish_loop(self):
        """
        Background thread that drains outbound queue and publishes messages.
        """
        while not self._stop_event.is_set():
            try:
                topic, payload, qos, retain = self.outbound_queue.get(timeout=0.5)
                self.client.publish(topic, payload, qos=qos, retain=retain)
            except queue.Empty:
                continue

    # ---------------------------------------------------------
    # Paho Callbacks
    # ---------------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected to {self.server}:{self.port}")
        else:
            print(f"[MQTT] Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print("[MQTT] Disconnected")
        if self.autoreconnect and not self._stop_event.is_set():
            print("[MQTT] Attempting reconnect...")
            while not self._stop_event.is_set():
                try:
                    time.sleep(2)
                    self.client.reconnect()
                    break
                except Exception:
                    continue

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        self.inbound_queue.put((msg.topic, payload))

        if self.on_message_callback:
            self.on_message_callback(msg.topic, payload)

    def _on_publish(self, client, userdata, mid):
        # This method is intentionally left empty as it serves as a placeholder
        # for the Paho MQTT on_publish callback. It can be overridden or extended
        # if specific behavior is needed(ACK , etc...) when a message is published.
        pass
