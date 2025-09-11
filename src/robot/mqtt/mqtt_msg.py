from __future__ import annotations


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

    def __lt__(self, other: "MqttMsg"):
        # Define an arbitrary but stable ordering for potential priority queues
        return self.id < other.id

