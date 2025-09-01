"""Distance sensor that performs a request/response over MQTT."""

import json
import threading
import uuid


class DistanceSensorTimeout(TimeoutError):
    pass


class DistanceSensor:
    """
    Distance sensor that performs a request/response over MQTT.

    Expected topics (customize to match Java library):
      - Request:  robot/{robot_id}/{channel}/sensors/distance/req
      - Response: robot/{robot_id}/{channel}/sensors/distance/resp
    Payloads carry a correlation_id so multiple concurrent sensors/requests
    can be disambiguated.
    """

    REQ_TOPIC_TMPL = "robot/{robot_id}/{channel}/sensors/distance/req"
    RESP_TOPIC_TMPL = "robot/{robot_id}/{channel}/sensors/distance/resp"

    def __init__(
        self,
        robot_id: str,
        robot_mqtt,
        channel: str = "v1",
        timeout_s: float = 2.0
    ):
        """
        :param robot_id: Unique robot id
        :param robot_mqtt: RobotMQTT helper that exposes publish() and
            subscribe()
            and delivers messages to handle_incoming(topic, payload)
        :param channel: Channel/version segment used in topics
        :param timeout_s: Max seconds to wait for a sensor reply
        """
        self.robot_id = robot_id
        self.channel = channel
        self.timeout_s = timeout_s

        # Synchronization
        self._lock = threading.Lock()
        self._waiters: dict[str, tuple[threading.Event, float | None]] = {
            # correlation_id -> (Event, value)
        }

        # MQTT wiring
        self._robot_mqtt = robot_mqtt
        resp_topic = self.RESP_TOPIC_TMPL.format(
            robot_id=robot_id, channel=channel
        )
        # Ensure we receive responses
        self._robot_mqtt.subscribe(resp_topic)

        # Register a handler with RobotMQTT to route only distance responses
        # here.
        # If RobotMQTT exposes a generic add_handler(topic_prefix, callback),
        # use it.
        # Otherwise, DistanceSensor exposes handle_incoming()
        # for RobotMQTT to call.
        if hasattr(self._robot_mqtt, "add_handler"):
            self._robot_mqtt.add_handler(resp_topic, self._on_mqtt_message)

    # If RobotMQTT doesn't support handler registration,
    # RobotMQTT should call this:
    def handle_incoming(self, topic: str, payload: str):
        """Pass-through for RobotMQTT to deliver messages to this sensor."""
        self._on_mqtt_message(topic, payload)

    # Internal MQTT message handler
    def _on_mqtt_message(self, topic: str, payload: str):
        # Only process our response topic
        expected = self.RESP_TOPIC_TMPL.format(
            robot_id=self.robot_id, channel=self.channel
        )
        if topic != expected:
            return

        try:
            data = json.loads(payload)
        except Exception:
            return

        corr = data.get("correlation_id")
        # distance in whatever units the simulator uses
        value = data.get("distance")

        if corr is None:
            return

        with self._lock:
            event_value = self._waiters.get(corr)
            if not event_value:
                return
            event, _ = event_value
            self._waiters[corr] = (event, value)
            event.set()

    def get_distance(self) -> float:
        """
        Publish a distance request and synchronously wait for the response.
        Raises DistanceSensorTimeout on timeout.
        """
        corr_id = uuid.uuid4().hex
        event = threading.Event()
        with self._lock:
            self._waiters[corr_id] = (event, None)

        req_topic = self.REQ_TOPIC_TMPL.format(
            robot_id=self.robot_id, channel=self.channel
        )
        payload = json.dumps({"correlation_id": corr_id})

        # Send request (QoS 0 by default; adjust if needed)
        self._robot_mqtt.publish(req_topic, payload)

        # Wait for response
        ok = event.wait(self.timeout_s)
        with self._lock:
            _, value = self._waiters.pop(corr_id, (None, None))

        if not ok or value is None:
            raise DistanceSensorTimeout(
                f"DistanceSensor timed out after {self.timeout_s:.2f}s"
            )

        return float(value)
