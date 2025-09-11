"""MQTT settings analogous to swarm.configs.MQTTSettings (Java).

Set these values before starting a robot to connect to the broker.
"""


class MQTTSettings:
    server: str | None = None
    port: int = 1883
    user_name: str | None = None
    password: str | None = None
    channel: str | None = None

    @classmethod
    def print(cls) -> None:
        print(f"server: {cls.server}")
        print(f"port: {cls.port}")
        print(f"username: {cls.user_name}")
        print(f"password: {cls.password}")
        print(f"channel: {cls.channel}")


__all__ = ["MQTTSettings"]
