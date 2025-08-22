import queue
import uuid
import paho.mqtt.client as mqtt


class MqttMsg:
    _next_id = 0

    def __init__(self, topic: str, message: str, qos: int = 0):
        self.id = MqttMsg._next_id
        MqttMsg._next_id += 1

        self.topic = topic
        self.message = message
        self.topic_groups = topic.split("/")
        self.channel = self.topic_groups[0] if len(self.topic_groups) > 1 else ""
        self.qos = qos

    def __repr__(self):
        return f"<MqttMsg id={self.id}, topic={self.topic}, message={self.message}, qos={self.qos}>"

    def __lt__(self, other):
        return self.id < other.id


class RobotMqttClient:


    def __init__(self, server: str, port: int, username: str, password: str, channel: str):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.channel = channel

        self.client_id = f"client_{uuid.uuid4().hex[:6]}"
        self.client = mqtt.Client(client_id=self.client_id, clean_session=True)

        if username and password:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.in_queue = queue.PriorityQueue()
        self.out_queue = queue.PriorityQueue()

        self.is_connected = False
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.server, self.port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"MQTT connect failed: {e}")
            self.is_connected = False
        else:
            self.is_connected = True
            print("MQTT: Connected")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            print("MQTT: Connection successful")
        else:
            print(f"MQTT: Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        print("MQTT: Connection lost")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        message = msg.payload.decode("utf-8")
        if message:
            # strip channel prefix
            t = topic.split("/", 1)[-1] if "/" in topic else topic
            self.in_queue.put(MqttMsg(t, message, msg.qos))

    def publish(self, topic: str, body: str, qos: int = 0, retained: bool = False):
        if not self.is_connected:
            raise RuntimeError("Not connected to broker")

        full_topic = f"{self.channel}/{topic}" if self.channel else topic
        self.client.publish(full_topic, body, qos=qos, retain=retained)
        self.out_queue.put(MqttMsg(full_topic, body, qos))

    def subscribe(self, topic: str, qos: int = 0):
        if not self.is_connected:
            raise RuntimeError("Not connected to broker")

        full_topic = f"{self.channel}/{topic}" if self.channel else topic
        self.client.subscribe(full_topic, qos)
        print(f"Subscribed to {full_topic}")

    def in_queue_get(self) -> MqttMsg | None:
        try:
            return self.in_queue.get_nowait()
        except queue.Empty:
            return None

    def out_queue_get(self) -> MqttMsg | None:
        try:
            return self.out_queue.get_nowait()
        except queue.Empty:
            return None
